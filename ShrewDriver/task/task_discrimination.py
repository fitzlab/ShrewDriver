from __future__ import division
import sys
sys.path.append("..")

import fileinput
import re
import math
import random
import time
import itertools
from constants.task_constants import *

from task_mixin import TaskMixin

from sequencer.sequencer_base import Sequencer
from trial import Trial

class TaskDiscrimination(TaskMixin):
    
    def __init__(self, training, shrewDriver):
        self.training = training
        self.shrewDriver = shrewDriver
        self.animalName = self.shrewDriver.animalName
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
            elif (self.initiation == Initiation.TAP or self.initiation == Initiation.TAP_ONSET) and \
                    (self.lastTapAt > self.stateStartTime or self.isTapping):
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
                if self.airPuffMode == AirPuffMode.SMINUS_OFFSET:
                    self.airPuff.puff()
                    self.training.logPlotAndAnalyze("Puff", time.time())

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
            #-- success condition --#
            if self.lastLickAt >= self.stateStartTime:
                if self.isHighRewardTrial:
                    self.training.dispenseReward(self.rewardBolusHardTrial/1000)
                else:
                    self.training.dispenseReward(self.rewardBolus/1000)
                
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
            if self.initiation == Initiation.TAP_ONSET:
                if not self.isTapping and now > self.stateEndTime:
                    self.stateDuration = self.initTime
                    self.changeState(States.INIT)
            else:
                if now > self.stateEndTime:
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

        #let Spike2 know which state we are now in
        self.training.send_stimcode(StateStimcodes[newState])

        #update end time
        self.stateEndTime = self.stateStartTime + self.stateDuration


        #print, just in case.
        msg = 'state changed to ' + str(States.whatis(newState)) + ' duration ' + str(self.stateDuration)
        if str(States.whatis(newState)) == 'SPLUS':
            msg += ' orientation ' + str(self.currentTrial.sPlusOrientation) 
        if str(States.whatis(newState)) == 'SMINUS':
            msg += ' orientation ' + str(self.currentTrial.sMinusOrientation) 
        print msg
    
    def checkFailOrAbort(self):
        # Checks if shrew licks when it shouldn't.
        # Used to check for aborts as well, but IR is no longer used, so that's out.
        # May be used in future with tap sensor.
        if self.isLicking or self.lastLickAt > self.stateStartTime:
            #any other time, licks are bad m'kay
            self.fail()

    
    def fail(self):
        self.stateDuration = self.timeoutFail
        
        if self.state != States.GRAY:
            self.trialResult = Results.TASK_FAIL
            if self.airPuffMode == AirPuffMode.TASK_FAIL_LICK or self.airPuffMode == AirPuffMode.BAD_LICK:
                self.training.airPuff.puff()
                self.training.logPlotAndAnalyze("Puff", time.time())
        else:
            self.trialResult = Results.FALSE_ALARM
            if self.airPuffMode == AirPuffMode.FALSE_ALARM_LICK or self.airPuffMode == AirPuffMode.BAD_LICK:
                self.training.airPuff.puff()
                self.training.logPlotAndAnalyze("Puff", time.time())

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


    #--- Interactive UI commands ---#
    def ui_dispense(self, rewardMicroliters):
        self.training.send_stimcode(STIMCODE_REWARD_GIVEN)
        self.training.dispenseReward(rewardMicroliters/1000)