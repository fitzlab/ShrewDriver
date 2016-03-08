from __future__ import division
import fileinput, re, math, sys, time

sys.path.append("./trial")
from Trial import Trial

sys.path.append("./global")
from Constants import *

sys.path.append("./util")
from Enumeration import *
import objectToString

sys.path.append("./sequencer")
from Sequencer import *

'''
A Task is a set of trial states and transitions, with logic to describe what happens in response to a shrew's actions.

This is where all the procedural logic lives.

Task types: There's actually only one, and it's called GNG, even though it can do nonmatch-to-sample. Awesome! 

'''

class Task(object):
    
    def __init__(self, taskType, training, shrewDriver):
        if taskType == TaskTypes.GNG:
            import TaskGoNoGo
            return TaskGoNoGo.TaskGoNoGo(training, shrewDriver)
        else:
            pass
        
    def makeStuff(self):
        #called from subclass inits
        
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
        
        self.commandStrings = [''] * len(stateSet)
        
        #load and record this session's settings
        self.loadAnimalSettings()
        self.writeSettingsFile()
        
        #send commands to prepare stimbot
        self.setUpCommands()
        
        #make a set of trial objects and a sequencer
        self.makeTrialSet()

        #set up the first trial
        if hasattr(self, 'sequencer'):
            self.currentTrial = self.sequencer.getNextTrial(None)
        self.prepareTrial()
        self.trialNum = 1
        
    def start(self):
        pass
    
    def prepareTrial(self):
        pass
    
    def checkStateProgression(self):
        pass
    
    def setUpCommands(self):
        #set up stimbot commands for later use
        self.training.stimSerial.write('screendist' + str(self.screenDistanceMillis) + '\n')
        for i in xrange(0, len(stateSet)):
            time.sleep(0.1) #wait a bit between long commands to make sure serial sends everything
            saveCommand = 'save' + str(i) + ' ' + self.commandStrings[i]
            self.training.stimSerial.write(saveCommand)
    
    def sensorUpdate(self, evtType, timestamp):
        if evtType == 'Ix':
            self.shrewPresent = True
            self.shrewEnteredAt = time.time()
        if evtType == 'Io':
            self.shrewPresent = False
        if evtType == 'Tx':
            self.isTapping = True
            self.lastTapAt = time.time()
        if evtType == 'To':
            self.isTapping = False
            self.lastTapAt = time.time()
        if evtType == 'Lx':
            self.isLicking = True
            self.lastLickAt = time.time()
        if evtType == 'Lo':
            self.isLicking = False
            #self.lastLickAt = time.time()
    
    def writeSettingsFile(self):
        self.settingsFilePath = self.shrewDriver.experimentPath + self.shrewDriver.sessionFileName + "_settings.txt" 
        self.summaryFilePath = self.shrewDriver.experimentPath + self.shrewDriver.sessionFileName + "_summary.txt" 
        self.settingsFile = open(self.settingsFilePath, 'w')
        self.settingsFile.write("States: " + str(stateSet) + "\n")
        thisAsString = objectToString.objectToString(self)
        self.settingsFile.write(thisAsString)
        self.settingsFile.close()
    
    def loadAnimalSettings(self):
        #Animal-relevant settings
        
        #--- First rig animals ---#
        
        if self.shrewDriver.animalName == 'Chico':
            print "Using settings for Chico!"
            self.sPlusOrientations = [135]
            self.sMinusOrientations = [180]
            self.sMinusPresentations = [0,1] #how many times to display the SMINUS
            self.guaranteedSPlus = True #is there always an SPLUS in the trial?
            self.sequenceType = Sequences.RANDOM
            self.initiation = Initiation.TAP
            
            self.timeoutFail = 6
            self.timeoutAbort = 6
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 6
            self.timeoutCorrectReject = 6
            
            self.initTime = 1
            
            self.variableDelayMin = 1.0
            self.variableDelayMax = 1.75
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.0 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.150
            self.rewardBolusHardTrial = 0.250
            
            #stimbot setup, including command strings for each state
            #note that grating states will have an extra command added later to specify orientation and phase.
            self.screenDistanceMillis = 25
            self.commandStrings[States.TIMEOUT] = 'ac pab px0 py0 sx12 sy12\n'
            self.commandStrings[States.INIT] = 'ac paw px0 py0 sx12 sy12\n'
            self.commandStrings[States.DELAY] = 'sx0 sy0\n'
            self.commandStrings[States.SMINUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.GRAY] = 'sx0 sy0\n'
            self.commandStrings[States.SPLUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.REWARD] = 'sx0 sy0\n'
            
        elif self.shrewDriver.animalName == 'Bernadette':
            print "Using settings for Bernadette!"
            self.sPlusOrientations = [90]
            self.sMinusOrientations = [135]
            self.sMinusPresentations = [0,1] #how many times to display the SMINUS
            self.guaranteedSPlus = True #is there always an SPLUS in the trial?
            self.sequenceType = Sequences.RANDOM_RETRY
            self.initiation = Initiation.TAP
            
            self.timeoutFail = 6
            self.timeoutAbort = 6
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 6
            self.timeoutCorrectReject = 0
            
            self.initTime = 1
            
            self.variableDelayMin = 1.0
            self.variableDelayMax = 1.75
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.0 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.100
            self.rewardBolusHardTrial = 0.200
        
            #stimbot setup, including command strings for each state
            #note that grating states will have an extra command added later to specify orientation and phase.
            self.screenDistanceMillis = 120
            self.commandStrings[States.TIMEOUT] = 'ac pab px0 py0 sx12 sy12\n'
            self.commandStrings[States.INIT] = 'ac paw px0 py0 sx12 sy12\n'
            self.commandStrings[States.DELAY] = 'sx0 sy0\n'
            self.commandStrings[States.SMINUS] = 'acgf sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.GRAY] = 'sx0 sy0\n'
            self.commandStrings[States.SPLUS] = 'acgf sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.REWARD] = 'sx0 sy0\n'
        
        
        #--- Second rig animals ---#
        
        elif self.shrewDriver.animalName == 'Clucker':
            print "Using settings for Clucker!"
            self.sPlusOrientations = [45]
            self.sMinusOrientations = [70]
            self.sMinusPresentations = [0,1] #how many times to display the SMINUS
            self.guaranteedSPlus = True #is there always an SPLUS in the trial?
            self.sequenceType = Sequences.RANDOM_RETRY
            self.initiation = Initiation.TAP
            
            self.timeoutFail = 6
            self.timeoutAbort = 6
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 6
            self.timeoutCorrectReject = 0
            
            self.initTime = 1
            
            self.variableDelayMin = 1.0
            self.variableDelayMax = 1.75
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.0 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.05 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.100
            self.rewardBolusHardTrial = 0.150
            
            #stimbot setup, including command strings for each state
            #note that grating states will have an extra command added later to specify orientation and phase.
            self.screenDistanceMillis = 25
            self.commandStrings[States.TIMEOUT] = 'ac pab px0 py0 sx12 sy12\n'
            self.commandStrings[States.INIT] = 'ac paw px0 py0 sx12 sy12\n'
            self.commandStrings[States.DELAY] = 'sx0 sy0\n'
            self.commandStrings[States.SMINUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.GRAY] = 'sx0 sy0\n'
            self.commandStrings[States.SPLUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.REWARD] = 'sx0 sy0\n'
            
        elif self.shrewDriver.animalName == 'Splinter':
            print "Using settings for Splinter!"
            self.sPlusOrientations = [90]
            self.sMinusOrientations = [45] #90-65 = 25 degree difference.
            self.sMinusPresentations = [0,1] #how many times to display the SMINUS
            self.guaranteedSPlus = True #is there always an SPLUS in the trial?
            self.sequenceType = Sequences.RANDOM_RETRY
            self.initiation = Initiation.TAP
            
            self.timeoutFail = 6
            self.timeoutAbort = 6
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 6
            self.timeoutCorrectReject = 0
            
            self.initTime = 1
            
            self.variableDelayMin = 1.0
            self.variableDelayMax = 1.75
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.0 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.05 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.100
            self.rewardBolusHardTrial = 0.150
            
            #stimbot setup, including command strings for each state
            #note that grating states will have an extra command added later to specify orientation and phase.
            self.screenDistanceMillis = 120
            self.commandStrings[States.TIMEOUT] = 'ac pab px0 py0 sx12 sy12\n'
            self.commandStrings[States.INIT] = 'ac paw px0 py0 sx12 sy12\n'
            self.commandStrings[States.DELAY] = 'sx0 sy0\n'
            self.commandStrings[States.SMINUS] = 'acgf sf0.25 tf0 jf0 ja0 px35 py0 sx999 sy999\n'
            self.commandStrings[States.GRAY] = 'sx0 sy0\n'
            self.commandStrings[States.SPLUS] = 'acgf sf0.25 tf0 jf0 ja0 px35 py0 sx999 sy999\n'
            self.commandStrings[States.REWARD] = 'sx0 sy0\n'
            
        
        elif self.shrewDriver.animalName == 'Peanut':
            print "Using settings for Peanut!"
            self.sPlusOrientations = [0]
            self.sMinusOrientations = [155] #180-155 = 25 degree difference.
            self.sMinusPresentations = [0,1] #how many times to display the SMINUS
            self.guaranteedSPlus = True #is there always an SPLUS in the trial?
            self.sequenceType = Sequences.RANDOM_RETRY
            self.initiation = Initiation.TAP
            
            self.timeoutFail = 6
            self.timeoutAbort = 6
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 6
            self.timeoutCorrectReject = 0
            
            self.initTime = 1
            
            self.variableDelayMin = 1.0
            self.variableDelayMax = 1.75
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.0 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.05 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.100
            self.rewardBolusHardTrial = 0.150
            
            #stimbot setup, including command strings for each state
            #note that grating states will have an extra command added later to specify orientation and phase.
            self.screenDistanceMillis = 120
            self.commandStrings[States.TIMEOUT] = 'ac pab px0 py0 sx12 sy12\n'
            self.commandStrings[States.INIT] = 'ac paw px0 py0 sx12 sy12\n'
            self.commandStrings[States.DELAY] = 'sx0 sy0\n'
            self.commandStrings[States.SMINUS] = 'acgf sf0.25 tf0 jf0 ja0 px35 py0 sx999 sy60\n'
            self.commandStrings[States.GRAY] = 'sx0 sy0\n'
            self.commandStrings[States.SPLUS] = 'acgf sf0.25 tf0 jf0 ja0 px35 py0 sx999 sy999\n'
            self.commandStrings[States.REWARD] = 'sx0 sy0\n'
            

        elif self.shrewDriver.animalName == 'Headfix':
            print "Using settings for headfix acclimation!"
            self.rewardCooldown = 0.5 #If shrew has not licked for this many seconds, make reward available.
            self.rewardBolus = 0.1
            
        else:
            raise Exception("ANIMAL NOT RECOGNIZED")
        
if __name__ == '__main__':
    print "run ShrewDriver.py instead!"
        