from __future__ import division
import time, threading, random, sys

sys.path.append("./devices")
from SerialPort import *

sys.path.append("./util")
from Enumeration import *
import objectToString

sys.path.append("./global")
from Constants import *

sys.path.append("./sequencer")
from Sequencer import *

from LivePlot import *
from ShrewDriver import *
from Trial import *

class Training():
    
    def __init__(self, shrewDriver):
        self.shrewDriver = shrewDriver
        
        self.stopFlag = False
        
        #start live plotting
        self.livePlot = LivePlot(self.shrewDriver.animalName)
        
        #start sensor serial
        self.arduinoSerial = SerialPort(self.shrewDriver.arduinoPortName)
        self.arduinoSerial.startReadThread()
        
        #start syringe pump serial
        self.syringeSerial = SerialPort(self.shrewDriver.syringePortName)
        self.syringeSerial.startReadThread()

        #start stim serial
        self.stimSerial = SerialPort(self.shrewDriver.stimPortName)
        self.stimSerial.startReadThread()

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
        
        #Animal-relevant settings
        if self.shrewDriver.animalName == 'Queen':
            print "Using settings for Queen!"
            self.sPlusOrientations = [135]
            self.sMinusOrientations = [45]
            self.sMinusPresentations = [0,0,1] #how many times to display the SMINUS
            self.guaranteedSPlus = False #is there always an SPLUS in the trial?
            self.sequenceType = Sequences.RANDOM_RETRY
            self.initiation = Initiation.IR
            
            self.timeoutFail = 20
            self.timeoutAbort = 10
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 10
            self.timeoutCorrectReject = 0
            
            self.initTime = 1
            
            self.variableDelayMin = 0.5
            self.variableDelayMax = 1.25
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.25 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.1 
            self.rewardBolusHardTrial = 0.2 
            
            #stimbot setup, including command strings for each state
            #note that grating states will have an extra command added later to specify orientation and phase.
            self.screenDistanceMillis = 120
            self.commandStrings[States.TIMEOUT] = 'ac pab px45 py0 sx12 sy12\n'
            self.commandStrings[States.INIT] = 'ac paw px45 py0 sx12 sy12\n'
            self.commandStrings[States.DELAY] = 'sx0 sy0\n'
            self.commandStrings[States.SMINUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.GRAY] = 'sx0 sy0\n'
            self.commandStrings[States.SPLUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.REWARD] = 'sx0 sy0\n'
            
        elif self.shrewDriver.animalName == 'Chico':
            print "Using settings for Chico!"
            self.sPlusOrientations = [45]
            self.sMinusOrientations = [45.01, 48.75, 52.5, 56.25, 60, 63.75, 67.5, 90, 135]
            self.sMinusPresentations = [1, 2] #how many times to display the SMINUS
            self.guaranteedSPlus = True #is there always an SPLUS in the trial?
            self.sequenceType = Sequences.BLOCK
            self.initiation = Initiation.IR
            
            self.timeoutFail = 10
            self.timeoutAbort = 10
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 10
            self.timeoutCorrectReject = 3
            
            self.initTime = 1
            
            self.variableDelayMin = 0.5
            self.variableDelayMax = 1.25
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.15
            self.rewardBolusHardTrial = 0.15
            
            #stimbot setup, including command strings for each state
            #note that grating states will have an extra command added later to specify orientation and phase.
            self.screenDistanceMillis = 120
            self.commandStrings[States.TIMEOUT] = 'as pab px0 py0 sx999 sy999\n'
            self.commandStrings[States.INIT] = 'as pab px0 py0 sx999 sy999\n'
            self.commandStrings[States.DELAY] = 'sx0 sy0\n'
            self.commandStrings[States.SMINUS] = 'acgf sf0.25 tf0 jf0 ja0 px45 py0 sx36 sy36\n'
            self.commandStrings[States.GRAY] = 'sx0 sy0\n'
            self.commandStrings[States.SPLUS] = 'acgf sf0.25 tf0 jf0 ja0 px45 py0 sx36 sy36\n'
            self.commandStrings[States.REWARD] = 'sx0 sy0\n'
            
        elif self.shrewDriver.animalName == 'Mercury':
            print "Using settings for Mercury!"
            self.sPlusOrientations = [0,0] 
            self.sMinusOrientations = [90, 135]
            self.sMinusPresentations = [0,1] #how many times to display the SMINUS
            self.guaranteedSPlus = False #is there always an SPLUS in the trial?
            self.sequenceType = Sequences.RANDOM
            self.initiation = Initiation.IR
             
            self.timeoutFail = 15
            self.timeoutAbort = 10
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 10
            self.timeoutCorrectReject = 0
            
            self.initTime = 1
            
            self.variableDelayMin = 0.5
            self.variableDelayMax = 1
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.0 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.15 
            self.rewardBolusHardTrial = 0.15
        
            #stimbot setup, including command strings for each state
            #note that grating states will have an extra command added later to specify orientation and phase.
            self.screenDistanceMillis = 120
            self.commandStrings[States.TIMEOUT] = 'ac pab px45 py0 sx12 sy12\n'
            self.commandStrings[States.INIT] = 'ac paw px45 py0 sx12 sy12\n'
            self.commandStrings[States.DELAY] = 'sx0 sy0\n'
            self.commandStrings[States.SMINUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.GRAY] = 'sx0 sy0\n'
            self.commandStrings[States.SPLUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.REWARD] = 'sx0 sy0\n'
            
        elif self.shrewDriver.animalName == 'Bernadette':
            print "Using settings for Bernadette!"
            self.sPlusOrientations = [90]
            self.sMinusOrientations = [0]
            self.sMinusPresentations = [0,0,1] #how many times to display the SMINUS
            self.guaranteedSPlus = False #is there always an SPLUS in the trial?
            self.sequenceType = Sequences.RANDOM
            self.initiation = Initiation.IR
            
            self.timeoutFail = 15
            self.timeoutAbort = 10
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 10
            self.timeoutCorrectReject = 0
            
            self.initTime = 1
            
            self.variableDelayMin = 0.5
            self.variableDelayMax = 1.25
            
            self.gratingDuration = 0.25
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.25 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.1 
            self.rewardBolusHardTrial = 0.2 
        
            #stimbot setup, including command strings for each state
            #note that grating states will have an extra command added later to specify orientation and phase.
            self.screenDistanceMillis = 120
            self.commandStrings[States.TIMEOUT] = 'ac pab px45 py0 sx12 sy12\n'
            self.commandStrings[States.INIT] = 'ac paw px45 py0 sx12 sy12\n'
            self.commandStrings[States.DELAY] = 'sx0 sy0\n'
            self.commandStrings[States.SMINUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.GRAY] = 'sx0 sy0\n'
            self.commandStrings[States.SPLUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
            self.commandStrings[States.REWARD] = 'sx0 sy0\n'
            
        else:
            raise Exception("ANIMAL NOT RECOGNIZED")
        
        #make a set of trial objects and a sequencer
        self.makeTrialSet()
        
        #start file logging
        self.logFilePath = self.shrewDriver.experimentPath + self.shrewDriver.sessionFileName + "_log.txt" 
        self.logFile = open(self.logFilePath, 'w')
        
        #Write settings file
        self.settingsFilePath = self.shrewDriver.experimentPath + self.shrewDriver.sessionFileName + "_settings.txt" 
        self.settingsFile = open(self.settingsFilePath, 'w')
        self.settingsFile.write("States: " + str(stateSet) + "\n")
        thisAsString = objectToString.objectToString(self)
        self.settingsFile.write(thisAsString)
        self.settingsFile.close()
        
        #set up stimbot commands for later use
        self.stimSerial.write('screendist' + str(self.screenDistanceMillis) + '\n')
        for i in xrange(0, len(stateSet)):
            time.sleep(0.1) #wait a bit between long commands to make sure serial sends everything
            saveCommand = 'save' + str(i) + ' ' + self.commandStrings[i]
            self.stimSerial.write(saveCommand)
        
        #turn screen on, if needed
        time.sleep(0.1) 
        self.stimSerial.write('screenon\n')
        
        #set up the first trial
        self.currentTrial = self.sequencer.getNextTrial(None)
        self.prepareTrial()
        self.trialNum = 1

    def prepareTrial(self):
        #prepare to run trial
        self.sMinusDisplaysLeft = self.currentTrial.numSMinus
        self.currentTrial.totalMicroliters = 0
        self.isHighRewardTrial = self.sMinusDisplaysLeft > min(self.sMinusPresentations)
        if random.uniform(0,1) < self.hintChance:
            self.doHint = True
        else:
            self.doHint = False
    
    def makeTrialSet(self):
        self.trialSet = []
        for numSMinus in self.sMinusPresentations:
            for sPlusOrientation in self.sPlusOrientations:
                for sMinusOrientation in self.sMinusOrientations:
                    if sMinusOrientation == sPlusOrientation:
                        #make sure SPLUS and SMINUS are different
                        continue
                    t = Trial()
                    t.numSMinus = numSMinus
                    t.sPlusOrientation = sPlusOrientation
                    t.sMinusOrientation = sMinusOrientation
                    
                    self.trialSet.append(t)
        
        print str(len(self.trialSet)) + " different trial conditions."
        
        self.sequencer = Sequencer(self.trialSet, self.sequenceType)
        
    def mainLoop(self):
        while not self.stopFlag:
            #check serial
            updates = self.arduinoSerial.getUpdates()
            for update in updates:
                self.processUpdates(update)
            #update state
            self.checkStateProgression()
            
            #get results from other serial threads
            #Prevents potential serial buffer overflow bugs
            bunchaCrap = self.syringeSerial.getUpdates()
            bunchaCrap = self.stimSerial.getUpdates()
            #Don't do anything with that information because it's crap
    
    def processUpdates(self, inputStr):
        updateTokens = str.split(inputStr)
        evtType = updateTokens[0]
        timestamp = float(updateTokens[1])
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
            self.lastLickAt = time.time()
        
        self.logAndPlot(evtType, timestamp)
    
    def logAndPlot(self, eventType, timestamp):
        self.livePlot.sigEvent.emit(eventType, timestamp)
        self.logFile.write(eventType + " " + str(timestamp) + "\n")
        
    def checkStateProgression(self):
        now = time.time()
        
        if self.state == States.INIT:
            #-- fail conditions --#
            if not self.shrewPresent:
                self.stateStartTime = now
            
            #Wait for the shrew to stop licking, unless its initiation type is LICK
            if self.initiation != Initiation.LICK:
                if self.isLicking or self.lastLickAt > self.stateStartTime:
                    self.stateStartTime = now
            
            #recompute state end time based on the above
            self.stateEndTime = self.stateStartTime + self.stateDuration
                
            #-- progression condition --#
            doneWaiting = False
            if self.initiation == Initiation.LICK and self.lastLickAt > self.stateStartTime:
                doneWaiting = True
            elif self.initiation == Initiation.TAP and self.lastTapAt > self.stateStartTime:
                doneWaiting = True
            elif self.initiation == Initiation.IR and now > self.stateEndTime:
                doneWaiting = True
            
            if doneWaiting:
                self.stateDuration = random.uniform(self.variableDelayMin, self.variableDelayMax)
                self.changeState(States.DELAY)
        
        if self.state == States.DELAY:
            #-- fail conditions --#
            self.checkFailOrAbort()
                
            #-- progression condition --#
            if now > self.stateEndTime:
                self.prepareGratingState()
            
        if self.state == States.SMINUS:
            #-- fail conditions --#
            self.checkFailOrAbort()
                
            #-- progression condition --#
            if now > self.stateEndTime:
                self.stateDuration = self.grayDuration
                self.changeState(States.GRAY)
                
        if self.state == States.GRAY:
            #-- fail conditions --#
            self.checkFailOrAbort()
                
            #-- progression condition --#
            if now > self.stateEndTime:
                if self.guaranteedSPlus or self.sMinusDisplaysLeft > 0:
                    #still more gratings to do, continue on
                    self.prepareGratingState()
                elif self.currentTrial.numSMinus < max(self.sMinusPresentations):
                    #OK, this happens when we have one SMINUS followed by an SPLUS,
                    #e.g. in Chico's task.
                    self.prepareGratingState()
                else:
                    #there's no SPLUS in this trial,
                    #and we did all the SMINUS displays. All done!
                    self.trialResult = Results.CORRECT_REJECT
                    self.stateDuration = self.timeoutCorrectReject
                    self.changeState(States.TIMEOUT)
            
        if self.state == States.SPLUS:
            #-- fail conditions --#
            self.checkFailOrAbort()
                
            #-- progression condition --#
            if now > self.stateEndTime:
                # Possibly dispense a small reward as a hint.
                if self.doHint:
                    self.dispenseHint()
                # go to reward state 
                self.stateDuration = self.rewardPeriod
                self.changeState(States.REWARD)
                
        if self.state == States.REWARD:
            #-- fail condition --#
            if not self.shrewPresent:
                self.abort()
            
            #-- success condition --#
            if self.lastLickAt > self.stateStartTime:
                self.dispenseReward()
                self.stateDuration = self.timeoutSuccess
                self.trialResult = Results.SUCCESS
                self.changeState(States.TIMEOUT)
                
            #-- progression condition --#
            if now > self.stateEndTime:
                self.stateDuration = self.timeoutNoResponse
                self.trialResult = Results.NO_RESPONSE
                self.changeState(States.TIMEOUT)
                
        if self.state == States.TIMEOUT:
            #-- progression condition --#
            if now > self.stateEndTime and self.shrewPresent:
                self.stateDuration = self.initTime
                self.changeState(States.INIT)
                
            
    def prepareGratingState(self): 
        #goes to either SMINUS or SPLUS.
        #this has its own function because it's called from both DELAY and GRAY.
        if self.sMinusDisplaysLeft > 0:
            self.stateDuration = self.gratingDuration
            self.changeState(States.SMINUS)
            self.sMinusDisplaysLeft -= 1
        else:
            #finished all SMINUS displays
            if self.guaranteedSPlus or self.currentTrial.numSMinus < max(self.sMinusPresentations) or \
                max(self.sMinusPresentations) == 0:
                #continue to SPLUS
                self.stateDuration = self.gratingDuration
                self.changeState(States.SPLUS)
            else:
                self.trialResult = Results.CORRECT_REJECT
                self.stateDuration = self.timeoutCorrectReject
                self.changeState(States.TIMEOUT)
    
    def changeState(self, newState):
        #runs every time a state changes
        #be sure to update self.stateDuration BEFORE calling this
        self.oldState = self.state
        self.state = newState
        self.stateStartTime = time.time()
        
        #if changed to timeout, reset trial params for the new trial
        if (newState == States.TIMEOUT):
            #tell UI about the trial that just finished
            print Results.whatis(self.trialResult) + "\n"
            self.shrewDriver.sigTrialEnd.emit(self.trialResult, self.oldState, \
                self.currentTrial.sPlusOrientation, self.currentTrial.sMinusOrientation, \
                self.currentTrial.numSMinus, self.doHint, self.currentTrial.totalMicroliters)
            
            #prepare next trial
            self.currentTrial = self.sequencer.getNextTrial(self.trialResult)
            self.prepareTrial()
            self.trialNum += 1
        
        #update screen
        if self.stateDuration > 0:
            if newState == States.SPLUS:
                #it's a grating, so call the base grating command
                #and add the orientation and phase
                phase = str(round(random.random(), 2))
                oriPhase = "sqr" + str(self.currentTrial.sPlusOrientation) + " ph" + phase
                self.stimSerial.write(str(self.state) + " " + oriPhase + "\n")
                self.logFile.write(oriPhase + " " + str(time.time()) + "\n")
            elif newState == States.SMINUS:
                phase = str(round(random.random(), 2))
                oriPhase = "sqr" + str(self.currentTrial.sMinusOrientation) + " ph" + phase
                self.stimSerial.write(str(self.state) + " " + oriPhase + "\n")
                self.logFile.write(oriPhase + " " + str(time.time()) + "\n")
            else:
                self.stimSerial.write(str(self.state) + "\n")
            
        self.stateEndTime = self.stateStartTime + self.stateDuration
        
        self.logAndPlot("State" + str(self.state), time.time())
        
        print 'state changed to ' + str(States.whatis(newState)) + ' duration ' + str(self.stateDuration)
    
    def dispenseHint(self):
        timestamp = time.time()
        self.syringeSerial.write(str(int(self.hintBolus*1000)) + "\n")
        self.logAndPlot("RL", time.time())
        self.currentTrial.totalMicroliters += int(self.hintBolus*1000)
        self.logFile.write("hint:" + str(self.hintBolus) + " " + str(timestamp) + "\n")
    
    def dispenseReward(self):
        timestamp = time.time()
        if self.isHighRewardTrial:
            self.syringeSerial.write(str(int(self.rewardBolusHardTrial*1000)) + "\n")
            self.currentTrial.totalMicroliters += int(self.rewardBolusHardTrial*1000)
            self.logFile.write("bolus:" + str(self.rewardBolusHardTrial) + " " + str(timestamp) + "\n")
        else:
            self.syringeSerial.write(str(int(self.rewardBolus*1000)) + "\n")
            self.currentTrial.totalMicroliters += int(self.rewardBolus*1000)
            self.logFile.write("bolus:" + str(self.rewardBolus) + " " + str(timestamp) + "\n")
        self.logAndPlot("RH", timestamp)
            
    def checkFailOrAbort(self):
        #Checks for when:
        #(1) Shrew licks when it shouldn't, or
        #(2) Shrew leaves the annex
        if self.isLicking or self.lastLickAt > self.stateStartTime:
            if self.state == States.DELAY and self.initiation == Initiation.LICK:
                #it's OK to lick during DELAY if they lick to initiate the trial
                pass
            else:
                #any other time, licks are bad m'kay
                self.fail()
        if not self.shrewPresent:
            self.abort()
    
    def fail(self):
        self.stateDuration = self.timeoutFail
        self.trialResult = Results.FAIL
        self.changeState(States.TIMEOUT)

    def abort(self):
        self.stateDuration = self.timeoutAbort
        self.trialResult = Results.ABORT
        self.changeState(States.TIMEOUT)
    
    def blackScreen(self):
        #used by "stop recording" to black out screen at end of experiment
        self.stimSerial.write('as pab px0 py0 sx999 sy999\n')
        time.sleep(0.05)
        self.stimSerial.write('screenoff\n')
    
    def stop(self):
        #end logfile
        self.logFile.close()
        
        #stop training thread and reset screen
        self.stopFlag = True
        time.sleep(0.01)
        self.blackScreen()
        time.sleep(0.5)
        
        #stop serial thread
        self.syringeSerial.close()
        self.arduinoSerial.close()
        self.stimSerial.close()
        
    
    def start(self):
        self.stopFlag = False
        
        self.stateDuration = self.initTime
        self.changeState(States.INIT)
        
        self.startTime = time.time()
        
        #threading /  main loop stuff goes here
        thread = threading.Thread(target=self.mainLoop)
        thread.daemon = True
        thread.start()

if __name__ == '__main__':
    print "run ShrewDriver.py instead!"
