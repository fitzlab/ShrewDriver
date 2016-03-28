import Sequencer, random

class SequencerBlock(Sequencer.Sequencer):
    
    def __init__(self, trialSet):
        self.trialSet = trialSet
        self.resetBlock()
        
    def resetBlock(self):
        self.block = []
        self.block.extend(self.trialSet)
        
    def getNextTrial(self, trialResult):
        if len(self.block) == 0:
            self.resetBlock()
        return self.block.pop(random.randint(0,len(self.block)-1))
        
