from __future__ import division

import fileinput, re, math, sys, random, time, itertools

import Task


sys.path.append("./sequencer")
from Sequencer import *

sys.path.append("./trial")
from Trial import Trial

class TaskGoNoGo(Task.Task):
    
    def __init__(self, training, shrewDriver):
        self.training = training
        self.shrewDriver = shrewDriver
        self.makeStuff()
        
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
        all_pairs = list(itertools.product(self.sPlusOrientations, self.sMinusOrientations))
        for numSMinus in self.sMinusPresentations:
            for p in all_pairs:
                (sPlusOrientation,sMinusOrientation) = p
                if abs(sPlusOrientation - sMinusOrientation) < 0.001:
                    #make sure SPLUS and SMINUS are different
                    continue
                
                t = Trial()
                t.numSMinus = numSMinus
                t.sPlusOrientation = sPlusOrientation
                t.sMinusOrientation = sMinusOrientation
                
                self.trialSet.append(t)
        
        print str(len(self.trialSet)) + " different trial conditions."
        
        self.sequencer = Sequencer(self.trialSet, self.sequenceType)
        if self.sequenceType == Sequences.INTERVAL or self.sequenceType == Sequences.INTERVAL_RETRY:
            self.sequencer.sequencer.easyOris = self.easyOris
            self.sequencer.sequencer.hardOris = self.hardOris
            self.sequencer.sequencer.numEasy = self.numEasy
            self.sequencer.sequencer.numHard = self.numHard
        
    def start(self):
        self.stateDuration = self.initTime
        self.changeState(States.INIT)
    
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
            if self.initiation == Initiation.LICK and self.lastLickAt > self.stateStartTime and not self.isLicking:
                #Shrew is supposed to lick, and it has, but it's not licking right now.
                if (now - self.lastLickAt) > 0.5:
                    #In fact, it licked at least half a second ago, so it should REALLY not be licking now. Let's proceed with the trial.
                    doneWaiting = True
            elif self.initiation == Initiation.TAP and (self.lastTapAt > self.stateStartTime or self.isTapping):
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
                    self.training.dispenseHint(self.hintBolus)
                # go to reward state 
                self.stateDuration = self.rewardPeriod
                self.changeState(States.REWARD)
                
        if self.state == States.REWARD:
            #-- fail condition --#
            if not self.shrewPresent:
                self.abort()
            
            #-- success condition --#
            if self.lastLickAt > self.stateStartTime:
                if self.isHighRewardTrial:
                    self.training.dispenseReward(self.rewardBolusHardTrial)
                else:
                    self.training.dispenseReward(self.rewardBolus)
                    
                self.stateDuration = self.timeoutSuccess
                self.trialResult = Results.HIT
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
    

    def changeState(self, newState):
        #runs every time a state changes
        #be sure to update self.stateDuration BEFORE calling this
        self.oldState = self.state
        self.state = newState
        self.stateStartTime = time.time()
        
        self.training.logPlotAndAnalyze("State" + str(self.state), time.time())        

        #if changed to timeout, reset trial params for the new trial
        if (newState == States.TIMEOUT):
            #tell UI about the trial that just finished
            print Results.whatis(self.trialResult) + "\n"
            self.shrewDriver.sigTrialEnd.emit()
            
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
                self.training.stimSerial.write(str(self.state) + " " + oriPhase + "\n")
                self.training.logPlotAndAnalyze(oriPhase, time.time())
            elif newState == States.SMINUS:
                phase = str(round(random.random(), 2))
                oriPhase = "sqr" + str(self.currentTrial.sMinusOrientation) + " ph" + phase
                self.training.stimSerial.write(str(self.state) + " " + oriPhase + "\n")
                self.training.logPlotAndAnalyze(oriPhase, time.time())
            else:
                self.training.stimSerial.write(str(self.state) + "\n")
            
        self.stateEndTime = self.stateStartTime + self.stateDuration
        
        msg = 'state changed to ' + str(States.whatis(newState)) + ' duration ' + str(self.stateDuration)
        if str(States.whatis(newState)) == 'SPLUS':
            msg += ' orientation ' + str(self.currentTrial.sPlusOrientation) 
        if str(States.whatis(newState)) == 'SMINUS':
            msg += ' orientation ' + str(self.currentTrial.sMinusOrientation) 
        print msg
    
    def checkFailOrAbort(self):
        #Checks for when:
        #(1) Shrew licks when it shouldn't, or
        #(2) Shrew leaves the annex
        if self.isLicking or self.lastLickAt > self.stateStartTime:
            #any other time, licks are bad m'kay
            self.fail()
        elif not self.shrewPresent and self.initiation != Initiation.TAP:
            self.abort()
    
    def fail(self):
        self.stateDuration = self.timeoutFail
        
        if self.state != States.GRAY:
            self.trialResult = Results.TASK_FAIL
        else:
            self.trialResult = Results.FALSE_ALARM
        
        self.changeState(States.TIMEOUT)

    def abort(self):
        self.stateDuration = self.timeoutAbort
        self.trialResult = Results.ABORT
        self.changeState(States.TIMEOUT)
    
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
    