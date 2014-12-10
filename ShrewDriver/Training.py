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
        self.livePlot = LivePlot()
        
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
        self.state = States.WAITLICK
        self.stateDuration = 1
        self.shrewPresent = False
        self.shrewEnteredAt = 0
        self.isLicking = False
        self.lastLickAt = 0
        self.stateStartTime = 0
        self.stateEndTime = 0

        #Animal-relevant settings
        if self.shrewDriver.animalName == 'Queen':
            print "Using settings for Queen!"
            self.sPlusOrientations = [135]
            self.sMinusOrientations = [45]
            self.sMinusPresentations = [0, 1] #how many times to display the SMINUS
            self.sequenceType = Sequences.RANDOM_RETRY
            
            self.timeoutFail = 10
            self.timeoutAbort = 10
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 10
            
            self.waitLickTime = 1
            
            self.variableDelayMin = 0.5 #Should be at least 0.5 seconds, see Tucker & Fitzpatrick 2006.
            self.variableDelayMax = 1.25
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.25 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.1 
            self.rewardBolusHardTrial = 0.2 
            
        elif self.shrewDriver.animalName == 'Chico':
            print "Using settings for Chico!"
            self.sPlusOrientations = [45]
            self.sMinusOrientations = [135]
            self.sMinusPresentations = [1, 2] #how many times to display the SMINUS
            self.sequenceType = Sequences.RANDOM_RETRY
            
            self.timeoutFail = 10
            self.timeoutAbort = 10
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 10
            
            self.waitLickTime = 1
            
            self.variableDelayMin = 0.5 #Should be at least 0.5 seconds, see Tucker & Fitzpatrick 2006.
            self.variableDelayMax = 1.25
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.25 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.1
            self.rewardBolusHardTrial = 0.2
            
        elif self.shrewDriver.animalName == 'Mercury':
            print "Using settings for Mercury!"
            self.sPlusOrientations = [0]
            self.sMinusOrientations = [90]
            self.sMinusPresentations = [0, 0, 0, 0, 1] #how many times to display the SMINUS
            self.sequenceType = Sequences.RANDOM
            
            self.timeoutFail = 10
            self.timeoutAbort = 10
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 10
            
            self.waitLickTime = 1
            
            self.variableDelayMin = 0.75 #Should be at least 0.5 seconds, see Tucker & Fitzpatrick 2006.
            self.variableDelayMax = 2
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.25 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.15 
            self.rewardBolusHardTrial = 0.25
        
        elif self.shrewDriver.animalName == 'Bernadette':
            print "Using settings for Bernadette!"
            self.sPlusOrientations = [90]
            self.sMinusOrientations = [0]
            self.sMinusPresentations = [0, 1] #how many times to display the SMINUS
            self.sequenceType = Sequences.RANDOM_RETRY
            
            self.timeoutFail = 10
            self.timeoutAbort = 10
            self.timeoutSuccess = 6
            self.timeoutNoResponse = 10
            
            self.waitLickTime = 1
            
            self.variableDelayMin = 0.5 #Should be at least 0.5 seconds, see Tucker & Fitzpatrick 2006.
            self.variableDelayMax = 1.25
            
            self.gratingDuration = 0.5
            self.grayDuration = 1
            self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
            
            self.hintChance = 0.25 #chance of sending a low reward at the start of the reward period
            
            self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
            self.rewardBolus = 0.1 
            self.rewardBolusHardTrial = 0.2 
        
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
        
        #set up the first trial
        self.currentTrial = self.sequencer.getNextTrial(None)
        self.prepareTrial()
        self.trialNum = 1

    def prepareTrial(self):
        #prepare to run trial
        self.sMinusDisplaysLeft = self.currentTrial.sMinusPresentation
        self.isHighRewardTrial = self.sMinusDisplaysLeft > min(self.sMinusPresentations)
        if random.uniform(0,1) < self.hintChance:
            self.doHint = True
        else:
            self.doHint = False
    
    def makeTrialSet(self):
        self.trialSet = []
        for sMinusPresentation in self.sMinusPresentations:
            for sPlusOrientation in self.sPlusOrientations:
                for sMinusOrientation in self.sMinusOrientations:
                    if sMinusOrientation == sPlusOrientation:
                        #make sure SPLUS and SMINUS are different
                        continue
                    t = Trial()
                    t.sMinusPresentation = sMinusPresentation
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
        #if shrew licks or leaves the IR beam, fail.
        
        if self.state == States.WAITLICK:
            #-- fail conditions --#
            if not self.shrewPresent:
                self.stateStartTime = now

            if self.isLicking or self.lastLickAt > self.stateStartTime:
                self.stateStartTime = now
                
            #-- progression condition --#
            self.stateEndTime = self.stateStartTime + self.stateDuration
            if now > self.stateEndTime:
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
                self.prepareGratingState()
            
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
                self.stateDuration = self.waitLickTime
                self.changeState(States.WAITLICK)
                
            
    def prepareGratingState(self): 
        #goes to either SMINUS or SPLUS.
        #this has its own function because it's called from both DELAY and GRAY.
        if self.sMinusDisplaysLeft > 0:
            self.stateDuration = self.gratingDuration
            self.changeState(States.SMINUS)
            self.sMinusDisplaysLeft -= 1
        else:
            #finished all SMINUS displays
            #continue to SPLUS
            self.stateDuration = self.gratingDuration
            self.changeState(States.SPLUS)
    
    def changeState(self, newState):
        #runs every time a state changes
        #be sure to update self.stateDuration BEFORE calling this
        self.state = newState
        self.stateStartTime = time.time()
        
        #if changed to timeout, reset trial params for the new trial
        if (newState == States.TIMEOUT):
            #tell UI about the trial that just finished
            self.shrewDriver.sigTrialEnd.emit(self.trialNum, Results.whatis(self.trialResult), \
                self.currentTrial.sPlusOrientation, self.currentTrial.sMinusOrientation, \
                self.currentTrial.sMinusPresentation, str(self.doHint))
            
            #prepare next trial
            self.currentTrial = self.sequencer.getNextTrial(self.trialResult)
            self.prepareTrial()
            self.trialNum += 1
        
        #update screen
        if (newState == States.DELAY) or \
                (newState == States.GRAY) or \
                (newState == States.REWARD):
            self.grayScreen()
        
        if (newState == States.TIMEOUT) or \
                (newState == States.WAITLICK):
            self.blackScreen()
        
        if (newState == States.SPLUS):
            self.grating(self.currentTrial.sPlusOrientation)
            
        if (newState == States.SMINUS):
            self.grating(self.currentTrial.sMinusOrientation)
        
        self.stateEndTime = self.stateStartTime + self.stateDuration
        
        self.logAndPlot("State" + str(self.state), time.time())
        
        print 'state changed to ' + str(States.whatis(newState))
    
    def dispenseHint(self):
        timestamp = time.time()
        self.syringeSerial.write(str(int(self.hintBolus*1000)) + "\n")
        self.logAndPlot("RL", time.time())
        self.logFile.write("hint:" + str(self.hintBolus) + " " + str(timestamp) + "\n")
    
    def dispenseReward(self):
        timestamp = time.time()
        if self.isHighRewardTrial:
            self.syringeSerial.write(str(int(self.rewardBolusHardTrial*1000)) + "\n")
            self.logFile.write("bolus:" + str(self.rewardBolusHardTrial) + " " + str(timestamp) + "\n")
        else:
            self.syringeSerial.write(str(int(self.rewardBolus*1000)) + "\n")
            self.logFile.write("bolus:" + str(self.rewardBolus) + " " + str(timestamp) + "\n")
        self.logAndPlot("RH", timestamp)
            
    def checkFailOrAbort(self):
        #Checks for when:
        #(1) Shrew licks when it shouldn't, or
        #(2) Shrew leaves the annex
        if self.isLicking or self.lastLickAt > self.stateStartTime:
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
    
    def grayScreen(self):
        self.stimSerial.write('g\n')
        
    def blackScreen(self):
        self.stimSerial.write('b\n')
        self.logFile.flush() #update log file after each trial ends
        
    def grating(self, orientation):
        self.stimSerial.write('o' + str(orientation) + "\n")
        self.logFile.write("ori" + str(orientation) + " " + str(time.time()) + "\n")
    
    def stop(self):
        #end logfile
        self.logFile.close()
        
        #stop training thread and reset screen
        self.stopFlag = True
        time.sleep(0.01)
        self.blackScreen()
        
        #stop serial thread
        self.ser.close()
        
    
    def start(self):
        self.stopFlag = False
        
        self.stateDuration = self.waitLickTime
        self.changeState(States.WAITLICK)
        
        self.startTime = time.time()
        
        #threading /  main loop stuff goes here
        thread = threading.Thread(target=self.mainLoop)
        thread.daemon = True
        thread.start()

if __name__ == '__main__':
    print "run ShrewDriver.py instead!"
