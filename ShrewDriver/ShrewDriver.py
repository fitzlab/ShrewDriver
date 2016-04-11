from __future__ import division

from PyQt4 import QtCore, QtGui, uic
import _winreg as winreg
import itertools
import glob
import time
import datetime
import os
import shutil
import fileinput
import operator

from devices.camera_reader import *

from util.enumeration import *
from constants.task_constants import *

from task.training import *
from ui.live_plot import *

#load the .ui files
ShrewDriver_class = uic.loadUiType("ui/shrewdriver.ui")[0]

'''
Run this file to start shrew training.
'''

class ShrewDriver(QtGui.QMainWindow, ShrewDriver_class):
    """
    UI logic. Tightly coupled to the Training class, see task/training.py.
    """
    
    #define signals that we will accept and use to update the UI
    sigTrialEnd = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        #make Qt window
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.training = None  # becomes a training instance when user hits Start
        
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
        self.sensorPortName = ""
        self.syringePortName = ""
        self.stimPortName = ""
        self.airPuffPortName = ""
        self.cameraID = 0
        
        self.trialHistory = []

        #dropdown actions
        self.cbAnimalName.currentIndexChanged.connect(self.setAnimal)
        self.cbSensors.currentIndexChanged.connect(self.setSensorPort)
        self.cbSyringePump.currentIndexChanged.connect(self.setSyringePort)
        self.cbVisualStim.currentIndexChanged.connect(self.setStimPort)
        self.cbAirPuff.currentIndexChanged.connect(self.setAirPuffPort)
        self.cbCameraID.currentIndexChanged.connect(self.setCameraID)

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

        #populate initial
        self.setAnimal()
        
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
            raise EnvironmentError
        for i in itertools.count():
            try:
                val = winreg.EnumValue(key, i)
                self.serialPorts.append(val[1])
            except EnvironmentError:
                break
        self.serialPorts = sorted(self.serialPorts)
        
        self.cbVisualStim.addItem("PsychoPy")
        self.cbAirPuff.addItem("None")

        for serialPort in self.serialPorts:
            self.cbSensors.addItem(serialPort)
            self.cbSyringePump.addItem(serialPort)
            self.cbVisualStim.addItem(serialPort)
            self.cbAirPuff.addItem(serialPort)


    def getAvailableCameras(self):
        cameraPath = 'HARDWARE\\DEVICEMAP\\VIDEO'
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, cameraPath)
        except WindowsError:
            raise EnvironmentError
        for i in itertools.count():
            try:
                val = winreg.EnumValue(key, i)
                self.cameraIDs.append(val[0])
            except EnvironmentError:
                break
        i = 0
        for cameraID in self.cameraIDs:
            self.cbCameraID.addItem(str(i))
            i += 1
    
    #-- Button Actions --# 
    def startRecording(self):
        
        if not self.isRecording:
            self.isRecording = True
            self.btnStartRecording.setText("Stop Recording")
            
            self.saveAnimalSettings()
            
            #start a new recording session by making a dir to put the data in
            self.makeSession()

            #start camera recording, live visualization, and training program
            self.startTraining()
            
        else:
            self.training.stop()
            self.isRecording = False
            self.btnStartRecording.setEnabled(False)
            #self.btnStartRecording.setText("Start Recording")
    
    def saveAnimalSettings(self):
        self.devicesPath = self.baseDataPath + self.animalName + "/devices.txt" 
        self.devicesFile = open(self.devicesPath, 'w')
        self.devicesFile.write('arduino ' + self.sensorPortName + "\n")
        self.devicesFile.write('syringe ' + self.syringePortName + "\n")
        self.devicesFile.write('stim ' + self.stimPortName + "\n")
        self.devicesFile.write('camera ' + str(self.cameraID) + "\n")
        self.devicesFile.close()
        
    def loadAnimalSettings(self):
        self.devicesPath = self.baseDataPath + self.animalName + "/devices.txt"
        fileinput.close() # ensure no fileinput is active already
        print 'Loading settings from ' + self.devicesPath
        if os.path.isfile(self.devicesPath):
            for line in fileinput.input(self.devicesPath):
                line = line.rstrip()
                toks = line.split(' ')
                if toks[0].lower() == 'arduino':
                    self.sensorPortName = toks[1]
                    self.setComboBox(self.cbSensors, toks[1])
                if toks[0].lower() == 'syringe':
                    self.syringePortName = toks[1]
                    self.setComboBox(self.cbSyringePump, toks[1])
                if toks[0].lower() == 'stim':
                    self.stimPortName = toks[1]
                    self.setComboBox(self.cbVisualStim, toks[1])
                if toks[0].lower() == 'camera':
                    self.cameraID = int(toks[1])
                    self.setComboBox(self.cbCameraID, toks[1])
    
    def setComboBox(self, cbx, value):
        #print "found value " + str(value) + " at index " + str(index)
        index = cbx.findText(str(value))
        cbx.setCurrentIndex(index)
    
    def makeSession(self):
        #make the dirs for a new recording session
        animalPath = self.baseDataPath + self.animalName + os.sep
        datePath = animalPath + self.dateStr + os.sep
        if not os.path.exists(datePath):
            os.makedirs(datePath)
        for i in range(1, 10000):
            sessionPath = datePath + str(i).zfill(4) + os.sep
            if not os.path.exists(sessionPath):
                self.sessionNumber = i
                os.makedirs(sessionPath)
                self.experimentPath = sessionPath
                break
        
        self.sessionFileName = self.animalName + '_' + self.dateStr + '_' + str(self.sessionNumber)

    
    #-- Signal Handlers --# 
    def trialEnd(self):
        self.updateResults()
    
    def updateResults(self):
        message = self.training.analyzer.get_results_str()
        message += "====\nTimestamp: " + str(time.time()) + "\n\n\n"
        
        if message is not None:
            self.txtTrialStats.setPlainText(message)
        
    
    #-- Dropdown Actions --# 
    def setAnimal(self):
        self.animalName = str(self.cbAnimalName.currentText())
        self.setWindowTitle(self.animalName + " - ShrewDriver")
        self.loadAnimalSettings()

    def setSensorPort(self):
        self.sensorPortName = str(self.cbSensors.currentText())

    def setSyringePort(self):
        self.syringePortName = str(self.cbSyringePump.currentText())

    def setStimPort(self):
        self.stimPortName = str(self.cbVisualStim.currentText())

    def setCameraID(self):
        self.cameraID = int(self.cbCameraID.currentText())

    def setAirPuffPort(self):
        self.airPuffPortName = str(self.cbAirPuff.currentText())

    #-- Menu Actions --#
    def quit(self):
        if self.training is not None:
            self.training.stop()
            time.sleep(0.5) #wait for everything to wrap up nicely
        self.close()
    
    def closeEvent(self, event):
        #happens when they click "X"
        self.quit()
        event.accept()

    def startTraining(self):
        self.training = Training(self)
        self.training.start()

    def setExperimentPath(self):
        self.experimentPath = ''

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myWindow = ShrewDriver(None)
    myWindow.show()
    app.exec_()

