from __future__ import division
import sys
sys.path.append("..")

from sequencer.sequencer_base import Sequencer
import sys
import random
from constants.task_constants import *

class SequencerRandomRetry(Sequencer):
    
    def __init__(self, trialSet):
        self.trialSet = trialSet
        self.currentTrial = None
        
    def getNextTrial(self, trialResult):
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