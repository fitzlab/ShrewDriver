from __future__ import division
from CameraReader import CameraReader
from Training import Training
from LivePlot import LivePlot
from PyQt4 import QtCore, QtGui, uic
import _winreg as winreg
import itertools, sys, glob, time, datetime, os, shutil

#load the .ui files
ShrewView_class = uic.loadUiType("mainwindow.ui")[0]

class ShrewView (QtGui.QMainWindow, ShrewView_class):
    
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
        self.serialPortName = ""
        self.cameraID = 0
        
        #init dropdown choices
        self.getAnimalDirs()
        self.getAvailableSerialPorts()
        self.getAvailableCameras()
        
        #menu actions
        self.actionQuit.triggered.connect(self.quit)
        
        #button actions
        self.btnStartRecording.clicked.connect(self.startRecording)
        
        #dropdown actions
        self.cbCameraID.currentIndexChanged.connect(self.setCameraID)
        self.cbAnimalName.currentIndexChanged.connect(self.setAnimal)
        self.cbSerialPort.currentIndexChanged.connect(self.setSerialPort)
        self.cbSyringePort.currentIndexChanged.connect(self.setSyringePort)
        

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
                #print str(val[1]) + ' ' + str(val[0])
                self.serialPorts.append(val[1])
            except EnvironmentError:
                break
        
        for serialPort in self.serialPorts:
            self.cbSerialPort.addItem(serialPort)
            self.cbSyringePort.addItem(serialPort)
    
    def getAvailableCameras(self):
        cameraPath = 'HARDWARE\\DEVICEMAP\\VIDEO'
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, cameraPath)
        except WindowsError:
            raise IterationError
        for i in itertools.count():
            try:
                val = winreg.EnumValue(key, i)
                #print str(val[1]) + ' ' + str(val[0])
                self.cameraIDs.append(val[0])
            except EnvironmentError:
                break
        i=0
        for cameraID in self.cameraIDs:
            self.cbCameraID.addItem(str(i))
            i+=1
    
    #-- Button Actions --# 
    def startRecording(self):
        self.setAnimal()
        self.setSerialPort()
        self.setSyringePort()
        self.setCameraID()
        
        if not self.isRecording:
            self.isRecording = True
            self.btnStartRecording.setText("Stop Recording")
            
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
    
    #-- Dropdown Actions --# 
    def setAnimal(self):
        self.animalName = str(self.cbAnimalName.currentText())
        #set path to the XML file containing instructions for this animal. 
        #Generate file from defaults if needed.
        self.xmlPath = self.baseDataPath + self.animalName + '/' + self.animalName + '.xml'
        if not os.path.isfile(self.xmlPath):
            shutil.copyfile('./default.xml', self.xmlPath)


    def setSerialPort(self):
        self.serialPortName = str(self.cbSerialPort.currentText())

    def setSyringePort(self):
        self.syringePortName = str(self.cbSyringePort.currentText())

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
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myWindow = ShrewView(None)
    myWindow.show()
    app.exec_()

