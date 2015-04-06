# A stimless task used during headfix acclimation

from __future__ import division

import fileinput, re, math, sys, random, time

import Task

sys.path.append("./sequencer")
from Sequencer import *

sys.path.append("./trial")
from Trial import Trial

class TaskHeadfix(Task.Task):
    
    def __init__(self, training, shrewDriver):
        self.training = training
        self.shrewDriver = shrewDriver
        self.makeStuff()
        
    def prepareTrial(self):
        pass
    
    def makeTrialSet(self):
        pass
        
    def start(self):
        self.changeState(States.REWARD)
    
    def checkStateProgression(self):
        now = time.time()
        
        if self.state == States.TIMEOUT:
            timeSinceLick = now - self.lastLickAt
            timeSinceStateStart = now - self.stateStartTime
            if timeSinceStateStart > self.rewardCooldown and not self.isLicking and timeSinceLick > self.rewardCooldown:
                #Shrew hasn't licked for a while, so make reward available
                self.changeState(States.REWARD)
               
        if self.state == States.REWARD:
            #Wait for the shrew to stop licking
            if self.lastLickAt > self.stateStartTime and self.lastLickAt != 0:
                self.training.dispenseReward(self.rewardBolus)
                self.changeState(States.TIMEOUT)
                
    def changeState(self, newState):
        #runs every time a state changes
        #self.training.logPlotAndAnalyze("State" + str(self.state), time.time())        
        self.stateStartTime = time.time()
        self.state = newState
        
        #if changed to timeout, reset trial params for the new trial
        if (newState == States.TIMEOUT):
            #tell UI about the trial that just finished
            print "Got bolus: " + str(self.rewardBolus) + " mL at " + str(time.time()) + "\n"
            #self.shrewDriver.sigTrialEnd.emit()
        
        print 'state changed to ' + str(States.whatis(newState))
    
    def checkFailOrAbort(self):
        pass
    
    def fail(self):
        pass

    def abort(self):
        pass
    
    def prepareGratingState(self): 
        pass
    
    def setUpCommands(self):
        #overwrite parent
        pass
        
    def makeTrialSet(self):
        #overwrite parent
        pass