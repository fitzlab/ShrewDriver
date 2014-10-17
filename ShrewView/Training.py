from __future__ import division
from Enumeration import Enumeration
from LivePlot import LivePlot
from SerialPort import SerialPort
import time, threading, random
import objectToString

stateSet = ['TIMEOUT', 'WAITLICK', 'DELAY', 'GRAY', 'SPLUS', 'SMINUS', 'REWARD']
States = Enumeration("States", stateSet)

'''
States:
    TIMEOUT - the black screen between trials. Longer timeout for failing, shorter for succeeding.
    WAITLICK - black screen until it has been a certain amount of time since the last lick.
    DELAY - gray screen of variable duration preceding the first grating presentation
    GRAY - gray screen between gratings, constant duration
    SPLUS - grating that is precedes rewardPeriod
    SMINUS - grating that does not precede rewardPeriod
    REWARD - gray screen during which reward is available. Same duration as GRAY.
'''

class Training():
    
    def __init__(self, shrewView):
        self.shrewView = shrewView
        
        self.stopFlag = False
        
        #start live plotting
        self.livePlot = LivePlot()
        
        #start serial
        self.ser = SerialPort(self.shrewView.serialPortName)
        self.ser.startReadThread()
        
        #behavior inits
        self.state = States.WAITLICK
        self.stateDuration = 1
        self.shrewPresent = False
        self.shrewEnteredAt = 0
        self.isLicking = False
        self.lastLickAt = 0
        self.stateStartTime = 0
        self.stateEndTime = 0
        
        #behavior variables
        self.sPlusOrientation = 0
        self.sMinusOrientations = [90] #Next step: add 112.5 and 67.5
        self.sMinusPresentations = [0, 1]
        self.sMinusOrientation = random.choice(self.sMinusOrientations)
        self.sMinusDisplaysLeft = random.choice(self.sMinusPresentations)
        
        self.timeoutFail = 10
        self.timeoutSuccess = 3
        self.timeoutNoResponse = 5

        self.waitLickTime = 1

        self.variableDelayMin = 0.5
        self.variableDelayMax = 1.25
        
        self.gratingDuration = 0.5
        self.grayDuration = 1
        self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!
        
        self.hintRewardChance = 0.5 #chance of sending a low reward at the start of the reward period
        
        #start file logging
        self.logFilePath = self.shrewView.experimentPath + self.shrewView.sessionFileName + "_log.txt" 
        self.logFile = open(self.logFilePath, 'w')
        
        #Write settings file
        self.settingsFilePath = self.shrewView.experimentPath + self.shrewView.sessionFileName + "_settings.txt" 
        self.settingsFile = open(self.settingsFilePath, 'w')
        self.settingsFile.write("States: " + str(stateSet) + "\n")
        thisAsString = objectToString.objectToString(self)
        self.settingsFile.write(thisAsString)
        self.settingsFile.close()
        
    def mainLoop(self):
        while not self.stopFlag:
            #check serial
            updates = self.ser.getUpdates()
            for update in updates:
                self.processUpdates(update)
            #update state
            self.checkStateProgression()
            
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
            if self.checkFail():
                self.fail()
                
            #-- progression condition --#
            if now > self.stateEndTime:
                self.prepareGratingState()
            
        if self.state == States.SMINUS:
            #-- fail conditions --#
            if self.checkFail():
                self.fail()
                
            #-- progression condition --#
            if now > self.stateEndTime:
                self.stateDuration = self.grayDuration
                self.changeState(States.GRAY)
                
        if self.state == States.GRAY:
            #-- fail conditions --#
            if self.checkFail():
                self.fail()
                
            #-- progression condition --#
            if now > self.stateEndTime:
                self.prepareGratingState()
            
        if self.state == States.SPLUS:
            #-- fail conditions --#
            if self.checkFail():
                self.fail()
                
            #-- progression condition --#
            if now > self.stateEndTime:
                # Possibly dispense a small reward as a hint.
                if random.uniform(0,1) < self.hintRewardChance:
                    self.dispenseHint()
                # go to reward state 
                self.stateDuration = self.rewardPeriod
                self.changeState(States.REWARD)
                
        if self.state == States.REWARD:
            #-- fail condition --#
            if not self.shrewPresent:
                self.fail()
            
            #-- success condition --#
            if self.lastLickAt > self.stateStartTime:
                self.dispenseReward()
                self.stateDuration = self.timeoutSuccess
                self.changeState(States.TIMEOUT)
                
            #-- progression condition --#
            if now > self.stateEndTime:
                self.stateDuration = self.timeoutNoResponse
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
            #reset SMINUS counter and orientation for next time
            self.sMinusDisplaysLeft = random.choice(self.sMinusPresentations)
            self.sMinusOrientation = random.choice(self.sMinusOrientations)
            #continue to SPLUS
            self.stateDuration = self.gratingDuration
            self.changeState(States.SPLUS)
    
    def changeState(self, newState):
        #runs every time a state changes
        #be sure to update self.stateDuration BEFORE calling this
        self.state = newState
        self.stateStartTime = time.time()
        
        #update screen
        if (newState == States.DELAY) or \
                (newState == States.GRAY) or \
                (newState == States.REWARD):
            self.grayScreen()
        
        if (newState == States.TIMEOUT) or \
                (newState == States.WAITLICK):
            self.blackScreen()
        
        if (newState == States.SPLUS):
            self.grating(self.sPlusOrientation)
            
        if (newState == States.SMINUS):
            self.grating(self.sMinusOrientation)
        
        self.stateEndTime = self.stateStartTime + self.stateDuration
        
        self.logAndPlot("State" + str(self.state), time.time())
        
        print 'state changed to ' + str(States.whatis(newState))
    
    def dispenseHint(self):
        self.ser.write('RL\n')
        self.logAndPlot("RL", time.time())
    
    def dispenseReward(self):
        self.ser.write('RH\n')
        self.logAndPlot("RH", time.time())
            
    def checkFail(self):
        #fail in most states happens when:
        #(1) Shrew licks when it shouldn't, or
        #(2) Shrew leaves the annex
        return self.isLicking or self.lastLickAt > self.stateStartTime or not self.shrewPresent
    
    def fail(self):
        self.stateDuration = self.timeoutFail
        self.changeState(States.TIMEOUT)
    
    def grayScreen(self):
        self.ser.write('g\n')
        
    def blackScreen(self):
        self.ser.write('b\n')
        
    def grating(self, orientation):
        self.ser.write('o' + str(orientation) + "\n")
    
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
    pass
