import Sequencer, random
import sys
sys.path.append("../global")
from Constants import *

class SequencerBlockRetry(Sequencer.Sequencer):
    
    def __init__(self, trialSet):
        self.trialSet = trialSet
        self.resetBlock()
        self.currentTrial = None
        
    def resetBlock(self):
        self.block = []
        self.block.extend(self.trialSet)
        
    def getNextTrial(self, trialResult):
        if len(self.block) == 0:
            self.resetBlock()
        if trialResult == Results.SUCCESS or trialResult == Results.CORRECT_REJECT or self.currentTrial == None:
            self.currentTrial = self.block.pop(random.randint(0,len(self.block)-1))
            return self.currentTrial
        else:
            return self.currentTrial
