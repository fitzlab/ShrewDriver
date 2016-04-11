from __future__ import division
import sys
sys.path.append("..")

from sequencer.sequencer_base import Sequencer
import random


class SequencerRandom(Sequencer):
    
    def __init__(self, trialSet):
        self.trialSet = trialSet
        
    def getNextTrial(self, trialResult):
        self.currentTrial = random.choice(self.trialSet)
        return self.currentTrial

