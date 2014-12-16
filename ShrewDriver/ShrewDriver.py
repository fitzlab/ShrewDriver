from __future__ import division
from PyQt4 import QtCore, QtGui, uic
import _winreg as winreg
import itertools, sys, glob, time, datetime, os, shutil, fileinput, operator

sys.path.append("./devices")
from CameraReader import *

sys.path.append("./util")
from Enumeration import *

sys.path.append("./global")
from Constants import *

from Training import *
from LivePlot import *

#load the .ui files
ShrewDriver_class = uic.loadUiType("mainwindow.ui")[0]

class ShrewDriver(QtGui.QMainWindow, ShrewDriver_class):
    
    #define signals that we will accept and use to update the UI

    sigTrialEnd = QtCore.pyqtSignal(int, int, float, float, int, bool, int)
    #result, resultState, sPlus, sMinus, numSMinus, hint, totalReward

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
        
        self.trialHistory = []
        
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
        self.serialPorts = sorted(self.serialPorts)
        
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
    def trialEnd(self, result, resultState, sPlus, sMinus, numSMinus, hint, totalMicroliters):
        #Receive data about a trial. Store it in the list of trials, then update the display
        t = Trial()
        t.result = result
        t.resultState = resultState
        t.sPlusOrientation = sPlus
        t.sMinusOrientation = sMinus
        t.numSMinus = numSMinus
        t.hint = hint
        t.totalMicroliters = totalMicroliters
        
        self.trialHistory.append(t)
        
        self.updateResults()
    
    def testTrialEnd(self):
        import random
        result = random.randint(0,3)
        oldState = random.randint(0,3)
        numSMinus = random.randint(0,2)
        hint = random.choice([True, False])
        microliters = random.choice([100, 200, 130])
        self.sigTrialEnd.emit(result, oldState, 3, 6, numSMinus, hint, microliters)
    
    def updateResults(self):
        # updates text in results textbox
        rewardMillis = 0
        numSuccess = 0
        numFail = 0
        numAbort = 0
        numNoResponse = 0
        
        #last 20
        successLast20 = 0
        failLast20 = 0

        #different failure states
        delayFails = 0
        sMinusFails = 0
        grayFails = 0
        sPlusFails = 0
        
        #different success types. Expand to include orientations later...
        noSminusHintSuccesses = 0
        oneSminusHintSuccesses = 0
        twoSminusHintSuccesses = 0
        noSminusNoHintSuccesses = 0
        oneSminusNoHintSuccesses = 0
        twoSminusNoHintSuccesses = 0
        
        #Go backwards through the last 20 trials
        for i in range(len(self.trialHistory)-1, -1, -1):
            t = self.trialHistory[i]
            
            rewardMillis += t.totalMicroliters / 1000
            
            if t.result == Results.ABORT:
                numAbort += 1
            if t.result == Results.NO_RESPONSE:
                numNoResponse += 1
            if t.result == Results.SUCCESS:
                numSuccess += 1
                
                if not t.hint and t.numSMinus == 0:
                    noSminusNoHintSuccesses += 1
                if  t.hint and t.numSMinus == 0:
                    noSminusHintSuccesses += 1
                if not t.hint and t.numSMinus == 1:
                    oneSminusNoHintSuccesses += 1
                if t.hint and t.numSMinus == 1:
                    oneSminusHintSuccesses += 1
                if not t.hint and t.numSMinus == 2:
                    twoSminusNoHintSuccesses += 1
                if t.hint and t.numSMinus == 2:
                    twoSminusHintSuccesses += 1
                
            if t.result == Results.FAIL:
                numFail += 1
                #now find out which state it failed in
                if t.resultState == States.DELAY:
                    delayFails += 1
                if t.resultState == States.SMINUS:
                    sMinusFails += 1
                if t.resultState == States.GRAY:
                    grayFails += 1
                if t.resultState == States.SPLUS:
                    sPlusFails += 1
                
            #work out results of the last 20 completed trials (exclude abort / no response)
            if successLast20+failLast20 < 20:
                #we're still in the 20 most recent completed trials
                if t.result == Results.SUCCESS:
                    successLast20 += 1
                if t.result == Results.FAIL:
                    failLast20 += 1
        
        if len(self.trialHistory) == 0 or (numSuccess + numFail) == 0 or (successLast20 + failLast20) == 0:
            self.txtTrialStats.setPlainText("Waiting for a response trial...")
            return
        
        message = "==================\n"
        message += "Shrew: " + self.animalName + "\n\n"
        
        #success rate
        percentSuccess = round(numSuccess / (numSuccess + numFail) * 100, 1)
        percentSuccessLast20 = round(successLast20 / (successLast20 + failLast20) * 100, 1)
        message += "=====\nOverall: " + str(percentSuccess)
        message += "% (" + str(numSuccess) + "/" + str(numSuccess + numFail) + ")\n"
        message += "Last 20 trials with responses: "
        message += str(percentSuccessLast20) + "%"
        message += " (" + str(successLast20) + "/" + str(successLast20 + failLast20) + ")\n\n"
        message += "Aborted Trials: " + str(numAbort) + "\n"
        message += "No-response Trials: " + str(numNoResponse) + "\n\n"
        message += "Total mL: " + str(rewardMillis) + "\n\n"
        
        message += "=====\nSuccess breakdown: \n\n"
        message += "0 sMinus: " + str(noSminusNoHintSuccesses) + "\n"
        message += "0 sMinus (Hint): " + str(noSminusHintSuccesses) + "\n\n"
        message += "1 sMinus: " + str(oneSminusNoHintSuccesses) + "\n"
        message += "1 sMinus (Hint): " + str(oneSminusHintSuccesses) + "\n\n"
        message += "2 sMinus: " + str(twoSminusNoHintSuccesses) + "\n"
        message += "2 sMinus (Hint): " + str(twoSminusHintSuccesses) + "\n"
        message += "\n"
        
        message += "=====\nFailure breakdown: \n\n"
        message += "DELAY: " + str(delayFails) + "\n"
        message += "SMINUS: " + str(sMinusFails) + "\n"
        message += "GRAY: " + str(grayFails) + "\n"
        message += "SPLUS: " + str(sPlusFails) + "\n\n"
        
        message += "=====\nSession: \n\n"
        message += self.dateStr + "\n"
        message += "Session " + str(self.sessionNumber) + "\n"
        message += "Timestamp: " + str(time.time()) + "\n"
        message += "\n==================\n"
        
        self.txtTrialStats.setPlainText(message)
        
    
    #-- Dropdown Actions --# 
    def setAnimal(self):
        self.animalName = str(self.cbAnimalName.currentText())
        self.setWindowTitle(self.animalName + " - ShrewDriver")
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
        self.cameraReader = CameraReader(self.cameraID, vidPath, self.animalName)
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
    myWindow = ShrewDriver(None)
    myWindow.show()
    app.exec_()

