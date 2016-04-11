from __future__ import division
import sys
sys.path.append("..")

from sequencer.sequencer_base import Sequencer
import random
from constants.task_constants import *

class SequencerStaircase(Sequencer):
    
    def __init__(self, trialSet):
        
        self.minSMinus = trialSet[0].sMinusOrientation
        self.maxSMinus = trialSet[0].sMinusOrientation
        
        for trial in trialSet:
            if trial.sMinusOrientation < self.minSMinus:
                self.minSMinus = trial.sMinusOrientation
            if trial.sMinusOrientation > self.maxSMinus:
                self.minSMinus = trial.sMinusOrientation
        
        self.currentTrial = None
        
        #search parameters
        self.highEstimate = self.maxSMinus
        self.lowEstimate = self.minSMinus
        self.resolution = 0.5
        self.stepSize = (self.highEstimate-self.lowEstimate)/2
    
    def getNextTrial(self, trialResult):
        # So, we want to use the existing trial structure, with its same number
        # of sMinus presentations and its sPlus orientation, but we're subbing in
        # an sMinus orientation of our choice (according to the staircase).
        
        newTrial = copy.copy(random.choice(self.trialSet))
        
        if self.currentTrial == None:
            self.currentTrial = random.choice(self.trialSet)
            return self.currentTrial
        else:
            if trialResult == Results.HIT or trialResult == Results.CORRECT_REJECT:
                #pick a new trial (possibly the same one again)
                self.currentTrial = random.choice(self.trialSet)
                return self.currentTrial
            else:
                #Failed, so repeat this trial
                return self.currentTrial
                
