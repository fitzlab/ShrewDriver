from __future__ import division
import sys
sys.path.append("..")


import time
import traceback
from constants.task_constants import *
from util.enumeration import *
from util.serialize import objectToString


from sequencer.sequencer_base import Sequencer

class TaskMixin(object):
    """Defines a set of functions used across all classes"""

    def make_stuff(self):
        #called from task class inits
        
        #behavior inits
        self.state = States.TIMEOUT
        self.stateDuration = 1
        self.shrewPresent = False
        self.shrewEnteredAt = 0
        self.isLicking = False
        self.lastLickAt = 0
        self.isTapping = False
        self.lastTapAt = 0
        self.stateStartTime = 0
        self.stateEndTime = 0

        self.showInteractUI = False

        self.commandStrings = [''] * len(stateSet)
        
        #load and record this session's settings
        self.load_animal_settings()
        self.write_settings_file()

        #send commands to prepare stimbot
        self.set_up_commands()

        #make a set of trial objects and a sequencer
        self.make_trial_set()

        #set up the first trial
        if hasattr(self, 'sequencer'):
            self.currentTrial = self.sequencer.getNextTrial(None)
        self.prepare_trial()
        self.trialNum = 1

    def set_up_commands(self):
        #set up stimbot commands for later use
        self.training.stimDevice.write('screendist' + str(self.screenDistanceMillis) + '\n')
        for i in xrange(0, len(stateSet)):
            time.sleep(0.1) #wait a bit between long commands to make sure serial sends everything
            saveCommand = 'save' + str(i) + ' ' + self.commandStrings[i]
            self.training.stimDevice.write(saveCommand)
    
    def sensor_update(self, evtType, timestamp):
        if evtType == 'Ix':
            self.shrewPresent = True
            self.shrewEnteredAt = time.time()
        if evtType == 'Io':
            self.shrewPresent = False
        if evtType.startswith('Tx'):
            self.isTapping = True
            self.lastTapAt = time.time()
        if evtType == 'To':
            self.isTapping = False
            self.lastTapAt = time.time()
        if evtType.startswith('Lx'):
            self.isLicking = True
            self.lastLickAt = time.time()
        if evtType == 'Lo':
            self.isLicking = False
            #self.lastLickAt = time.time()
    
    def write_settings_file(self):
        self.settingsFilePath = self.shrewDriver.experimentPath + self.shrewDriver.sessionFileName + "_settings.txt" 
        self.summaryFilePath = self.shrewDriver.experimentPath + self.shrewDriver.sessionFileName + "_summary.txt" 
        self.settingsFile = open(self.settingsFilePath, 'w')
        self.settingsFile.write("States: " + str(stateSet) + "\n")
        thisAsString = objectToString(self)
        self.settingsFile.write(thisAsString)
        self.settingsFile.close()
    
    def load_animal_settings(self):
        try:
            print "Importing settings from shrew/" + self.animalName.lower() + ".py"
            sys.stdout.flush()
            importStatement = "from shrew." + self.animalName.lower() + " import load_parameters"
            exec(importStatement)
            eval("load_parameters(self)")  # this is just an eval so the code editor won't complain about missing imports

        except():
            print "Error - couldn't load shrew/" + self.animalName.lower() + ".py!"
            print "Check that the file exists and has a load_settings function."
            traceback.print_exc()
            raise()
