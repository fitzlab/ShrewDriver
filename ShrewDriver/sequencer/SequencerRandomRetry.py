import Sequencer
import sys, random
sys.path.append("../global")
from Constants import *

class SequencerRandomRetry(Sequencer.Sequencer):
    
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