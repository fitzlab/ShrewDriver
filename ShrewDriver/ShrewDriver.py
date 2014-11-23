from __future__ import division
from PyQt4 import QtCore, QtGui, uic
import _winreg as winreg
import itertools, sys, glob, time, datetime, os, shutil, fileinput, operator

sys.path.append("./devices")
from CameraReader import *

from Training import *
from LivePlot import *

#load the .ui files
ShrewDriver_class = uic.loadUiType("mainwindow.ui")[0]

class ShrewDriver(QtGui.QMainWindow, ShrewDriver_class):
    
    #define signals that we will accept and use to update the UI
    sigTrialEnd = QtCore.pyqtSignal(int, str, int, int, int, str)
    
    def __init__(self, parent=None):
        #make Qt window
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        
        #set class variables
        self.isRecording = False
        self.baseDataPath = "../../ShrewData/"
        self.dateStr = str(datetime.date.today())
        self.sessionNumber = 1
        self.experimentPath = "" #set when recording starts
        self.sessionFileName = "" #likewise
        
        self.serialPorts = []
        self.animalNames = []
        self.cameraIDs = []
        
        self.animalName = ""
        self.arduinoPortName = ""
        self.syringePortName = ""
        self.stimPortName = ""
        self.cameraID = 0
        
        #init dropdown choices
        self.getAnimalDirs()
        self.getAvailableSerialPorts()
        self.getAvailableCameras()
        
        #menu actions
        self.actionQuit.triggered.connect(self.quit)
        
        #button actions
        self.btnStartRecording.clicked.connect(self.startRecording)
        
        #signal actions 
        self.sigTrialEnd.connect(self.trialEnd)
        
        #dropdown actions
        self.cbCameraID.currentIndexChanged.connect(self.setCameraID)
        self.cbAnimalName.currentIndexChanged.connect(self.setAnimal)
        self.cbArduinoPort.currentIndexChanged.connect(self.setArduinoPort)
        self.cbSyringePort.currentIndexChanged.connect(self.setSyringePort)
        self.cbStimPort.currentIndexChanged.connect(self.setStimPort)
        
        #trial history table
        self.trialHistoryModel = TrialHistoryModel(self) 
        self.tblTrialHistory.setModel(self.trialHistoryModel)

        #ui crud, probably unimportant
        self.tblTrialHistory.setShowGrid(False)
        vh = self.tblTrialHistory.verticalHeader()
        vh.setVisible(False)
        hh = self.tblTrialHistory.horizontalHeader()
        hh.setStretchLastSection(True)
        self.tblTrialHistory.resizeColumnsToContents()
        self.tblTrialHistory.setSortingEnabled(True)
        
    #-- Init Functions --# 
    def getAnimalDirs(self):
        self.animalDirs = glob.glob(self.baseDataPath + '*')
        for animalDir in self.animalDirs:
            if os.path.isdir(animalDir):
                namePos = animalDir.rfind("\\")+1
                animalName = animalDir[namePos:]
                self.cbAnimalName.addItem(animalName)
        
    def getAvailableSerialPorts(self):
        #Uses the Win32 registry to return a iterator of serial 
        #(COM) ports existing on this computer.
        serialPath = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, serialPath)
        except WindowsError:
            raise IterationError
        for i in itertools.count():
            try:
                val = winreg.EnumValue(key, i)
                self.serialPorts.append(val[1])
            except EnvironmentError:
                break
        
        for serialPort in self.serialPorts:
            self.cbArduinoPort.addItem(serialPort)
            self.cbSyringePort.addItem(serialPort)
            self.cbStimPort.addItem(serialPort)
    
    def getAvailableCameras(self):
        cameraPath = 'HARDWARE\\DEVICEMAP\\VIDEO'
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, cameraPath)
        except WindowsError:
            raise IterationError
        for i in itertools.count():
            try:
                val = winreg.EnumValue(key, i)
                self.cameraIDs.append(val[0])
            except EnvironmentError:
                break
        i=0
        for cameraID in self.cameraIDs:
            self.cbCameraID.addItem(str(i))
            i+=1
    
    #-- Button Actions --# 
    def startRecording(self):
        if not self.isRecording:
            self.isRecording = True
            self.btnStartRecording.setText("Stop Recording")
            
            self.saveAnimalSettings()
            
            #start a new recording session by making a dir to put the data in
            self.makeSession()
            
            #start camera recording, live visualization, and training program
            self.startCamera()
            self.startLivePlot()
            self.startTraining()
            
        else:
            self.stopRecording()
            self.training.stop()
            self.isRecording = False
            self.btnStartRecording.setText("Start Recording")
    
    def saveAnimalSettings(self):
        self.devicesPath = self.baseDataPath + self.animalName + "/devices.txt" 
        self.devicesFile = open(self.devicesPath, 'w')
        self.devicesFile.write('arduino ' + self.arduinoPortName + "\n")
        self.devicesFile.write('syringe ' + self.syringePortName + "\n")
        self.devicesFile.write('stim ' + self.stimPortName + "\n")
        self.devicesFile.write('camera ' + str(self.cameraID) + "\n")
        self.devicesFile.close()
        
    def loadAnimalSettings(self):
        self.devicesPath = self.baseDataPath + self.animalName + "/devices.txt"
        print 'Loading settings from ' + self.devicesPath
        if os.path.isfile(self.devicesPath):
            for line in fileinput.input(self.devicesPath):
                line = line.rstrip()
                toks = line.split(' ')
                if toks[0].lower() == 'arduino':
                    self.arduinoPortName = toks[1]
                    self.setComboBox(self.cbArduinoPort, toks[1])
                if toks[0].lower() == 'syringe':
                    self.syringePortName = toks[1]
                    self.setComboBox(self.cbSyringePort, toks[1])
                if toks[0].lower() == 'stim':
                    self.stimPortName = toks[1]
                    self.setComboBox(self.cbStimPort, toks[1])
                if toks[0].lower() == 'camera':
                    self.cameraID = int(toks[1])
                    self.setComboBox(self.cbCameraID, toks[1])
    
    def setComboBox(self, cbx, value):
        #print "found value " + str(value) + " at index " + str(index)
        index = cbx.findText(str(value))
        cbx.setCurrentIndex(index)
    
    def makeSession(self):
        #make the dirs for a new recording session
        animalPath = self.baseDataPath + self.animalName + '/'
        datePath = animalPath + self.dateStr + '/'
        if not os.path.exists(datePath):
            os.makedirs(datePath)
        for i in range(1,10000):
            sessionPath = datePath + str(i).zfill(4) + '/'
            if not os.path.exists(sessionPath):
                self.sessionNumber = i
                os.makedirs(sessionPath)
                self.experimentPath = sessionPath
                break
        
        self.sessionFileName = self.animalName + '_' + self.dateStr + '_' + str(self.sessionNumber)
        
    def stopRecording(self):
        self.cameraReader.stopFlag = True
    
    #-- Signal Handlers --# 
    def trialEnd(self, trialNum, result, sPlus, sMinus, numSMinus, hint):
        self.trialHistoryModel.addRow(trialNum, result, sPlus, sMinus, numSMinus, hint)
        
    #-- Dropdown Actions --# 
    def setAnimal(self):
        self.animalName = str(self.cbAnimalName.currentText())
        self.loadAnimalSettings()

    def setArduinoPort(self):
        self.arduinoPortName = str(self.cbArduinoPort.currentText())

    def setSyringePort(self):
        self.syringePortName = str(self.cbSyringePort.currentText())

    def setStimPort(self):
        self.stimPortName = str(self.cbStimPort.currentText())

    def setCameraID(self):
        self.cameraID = int(self.cbCameraID.currentText())

    #-- Menu Actions --#
    def quit(self):
        self.stopRecording()
        self.training.stop()
        time.sleep(0.3) #wait for everything to wrap up nicely
        self.close()
    
    def closeEvent(self, event):
        #happens when they click "X"
        self.quit()
        event.accept()

    #-- Real Work --#
    def startCamera(self):
        #begin live view and recording from camera
        vidPath = self.experimentPath + self.sessionFileName + '.avi'
        print 'Recording video to ' + vidPath
        self.cameraReader = CameraReader(self.cameraID, vidPath)
        self.cameraReader.startReadThread()
    
    def startLivePlot(self):
        pass
        #self.livePlot = LivePlot()
    
    def startTraining(self):
        self.training = Training(self)
        self.training.start()
        
    def setExperimentPath(self):
        self.experimentPath = ''
    


class TrialHistoryModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None): 
        QtCore.QAbstractTableModel.__init__(self, parent) 
        self.arraydata = []
        self.headerdata = ['Trial', 'Result', 'sPlus', 'sMinus', '#sMinus', 'Hint']
 
    def rowCount(self, parent): 
        return len(self.arraydata) 
 
    def columnCount(self, parent): 
        return len(self.headerdata) 
 
    def data(self, index, role): 
        if not index.isValid(): 
            return QtCore.QVariant() 
        elif role != QtCore.Qt.DisplayRole: 
            return QtCore.QVariant() 
        if len(self.arraydata) == 0:
            return None
        return QtCore.QVariant(self.arraydata[index.row()][index.column()]) 

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.headerdata[col])
        return QtCore.QVariant()

    def addRow(self, trialNum, result, sPlus, sMinus, numSMinus, hint):
        self.arraydata.append([trialNum, result, sPlus, sMinus, numSMinus, hint])
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def sort(self, Ncol, order):
        """Sort table by given column number.
        """
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))        
        if order == QtCore.Qt.DescendingOrder:
            self.arraydata.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myWindow = ShrewDriver(None)
    myWindow.show()
    app.exec_()

