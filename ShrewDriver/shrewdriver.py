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
from ui.interact import InteractUI

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
        self.cbAnimalName.currentIndexChanged.connect(self.set_animal)
        self.cbSensors.currentIndexChanged.connect(self.set_sensor_port)
        self.cbSyringePump.currentIndexChanged.connect(self.set_syringe_port)
        self.cbVisualStim.currentIndexChanged.connect(self.set_stim_port)
        self.cbAirPuff.currentIndexChanged.connect(self.set_air_puff_port)
        self.cbCameraID.currentIndexChanged.connect(self.set_camera_ID)

        #init dropdown choices
        self.get_animal_dirs()
        self.get_available_serial_ports()
        self.get_available_cameras()
        
        #menu actions
        self.actionQuit.triggered.connect(self.quit)
        
        #button actions
        self.btnStartRecording.clicked.connect(self.start_recording)
        
        #signal actions 
        self.sigTrialEnd.connect(self.trial_end)

        #populate initial
        self.set_animal()
        
    #-- Init Functions --# 
    def get_animal_dirs(self):
        self.animalDirs = glob.glob(self.baseDataPath + '*')
        for animalDir in self.animalDirs:
            if os.path.isdir(animalDir):
                namePos = animalDir.rfind("\\")+1
                animalName = animalDir[namePos:]
                self.cbAnimalName.addItem(animalName)
        
    def get_available_serial_ports(self):
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


    def get_available_cameras(self):
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
    def start_recording(self):
        
        if not self.isRecording:
            self.isRecording = True
            self.btnStartRecording.setText("Stop Recording")
            
            self.save_animal_settings()
            
            #start a new recording session by making a dir to put the data in
            self.make_session()

            #start camera recording, live visualization, and training program
            self.start_training()
            
        else:
            self.training.stop()
            self.isRecording = False
            self.btnStartRecording.setEnabled(False)
            #self.btnStartRecording.setText("Start Recording")
    
    def save_animal_settings(self):
        self.devicesPath = self.baseDataPath + self.animalName + "/devices.txt" 
        self.devicesFile = open(self.devicesPath, 'w')
        self.devicesFile.write('arduino ' + self.sensorPortName + "\n")
        self.devicesFile.write('syringe ' + self.syringePortName + "\n")
        self.devicesFile.write('stim ' + self.stimPortName + "\n")
        self.devicesFile.write('camera ' + str(self.cameraID) + "\n")
        self.devicesFile.write('airpuff ' + str(self.airPuffPortName) + "\n")
        self.devicesFile.close()
        
    def load_animal_settings(self):
        self.devicesPath = self.baseDataPath + self.animalName + "/devices.txt"
        fileinput.close() # ensure no fileinput is active already
        print 'Loading settings from ' + self.devicesPath
        if os.path.isfile(self.devicesPath):
            for line in fileinput.input(self.devicesPath):
                line = line.rstrip()
                toks = line.split(' ')
                if toks[0].lower() == 'arduino':
                    self.sensorPortName = toks[1]
                    self.set_combo_box(self.cbSensors, toks[1])
                if toks[0].lower() == 'syringe':
                    self.syringePortName = toks[1]
                    self.set_combo_box(self.cbSyringePump, toks[1])
                if toks[0].lower() == 'stim':
                    self.stimPortName = toks[1]
                    self.set_combo_box(self.cbVisualStim, toks[1])
                if toks[0].lower() == 'camera':
                    self.cameraID = int(toks[1])
                    self.set_combo_box(self.cbCameraID, toks[1])
                if toks[0].lower() == 'airpuff':
                    if toks[1] == "None":
                        self.airPuffPortName = None
                    else:
                        self.airPuffPortName = toks[1]
                    self.set_combo_box(self.cbAirPuff, toks[1])
    
    def set_combo_box(self, cbx, value):
        #print "found value " + str(value) + " at index " + str(index)
        index = cbx.findText(str(value))
        cbx.setCurrentIndex(index)
    
    def make_session(self):
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
    def trial_end(self):
        self.update_results()
    
    def update_results(self):
        message = self.training.analyzer.get_results_str()

        if message is not None:
            self.txtTrialStats.setPlainText(message)
        
    
    #-- Dropdown Actions --# 
    def set_animal(self):
        self.animalName = str(self.cbAnimalName.currentText())
        self.setWindowTitle(self.animalName + " - ShrewDriver")
        self.load_animal_settings()

    def set_sensor_port(self):
        self.sensorPortName = str(self.cbSensors.currentText())

    def set_syringe_port(self):
        self.syringePortName = str(self.cbSyringePump.currentText())

    def set_stim_port(self):
        self.stimPortName = str(self.cbVisualStim.currentText())

    def set_camera_ID(self):
        self.cameraID = int(self.cbCameraID.currentText())

    def set_air_puff_port(self):
        self.airPuffPortName = str(self.cbAirPuff.currentText())

    #-- Menu Actions --#
    def quit(self):
        if self.training is not None:
            self.training.stop()
            time.sleep(0.5) #wait for everything to wrap up nicely
        self.close()

    def closeEvent(self, event):
        #Overrides the PyQt function of the same name, so you can't rename this.
        #Happens when user clicks "X".
        self.quit()
        event.accept()

    #-- Other --#
    def start_training(self):
        self.training = Training(self)
        self.training.start()

    def show_interact_ui(self, task):
        """If allowed, this will be shown when the user starts recording. Called by training.py."""
        self.interactUI = InteractUI()
        self.interactUI.set_task(task)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myWindow = ShrewDriver(None)
    myWindow.show()
    app.exec_()

