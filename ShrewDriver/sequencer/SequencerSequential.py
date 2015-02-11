import Sequencer, random

class SequencerSequential(Sequencer.Sequencer):
    
    def __init__(self, trialSet):
        self.trialSet = trialSet
        self.trialIndex = 0
        
    def getNextTrial(self, trialResult):
        self.currentTrial = self.trialSet[self.trialIndex]
        self.trialIndex += 1
        if self.trialIndex > len(self.trialSet):
            self.trialIndex = 0
        return self.currentTrial
        
