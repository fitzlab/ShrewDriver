import Sequencer, random

class SequencerRandom(Sequencer.Sequencer):
    
    def __init__(self, trialSet):
        self.trialSet = trialSet
        
    def getNextTrial(self, trialResult):
        self.currentTrial = random.choice(self.trialSet)
        return self.currentTrial
        
