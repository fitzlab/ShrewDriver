import Sequencer
import sys, random
sys.path.append("../global")
from Constants import *

#Gives the shrew a free S+ following each correct reject.
#Retry on any failure.

class SequencerSPlusForRejectRetry(Sequencer.Sequencer):
    
    def __init__(self, trialSet):
        self.trialSet = trialSet
        self.currentTrial = None
        self.sPlusTrial = None
        self.isFreeSPlus = False #keep track of whether we're on a freebie trial or not
        for t in self.trialSet:
            print str(t.numSMinus)
            if t.numSMinus == 0:
                self.sPlusTrial = t
                
        
    def getNextTrial(self, trialResult):
        if self.currentTrial == None:
            self.currentTrial = random.choice(self.trialSet)
            return self.currentTrial
        else:
            if not self.isFreeSPlus:
                if trialResult == Results.HIT:
                    #pick a new trial (possibly the same one again)
                    self.currentTrial = random.choice(self.trialSet)
                    return self.currentTrial
                elif  trialResult == Results.CORRECT_REJECT:
                    #give shrew the free S+ trial
                    self.currentTrial = self.sPlusTrial
                    self.isFreeSPlus = True
                    return self.currentTrial
                else:
                    #Failed, so repeat this trial
                    return self.currentTrial
            else:
                #this trial was an S+ following a correct reject
                if trialResult == Results.HIT:
                    self.isFreeSPlus = False
                    #pick a new trial
                    self.currentTrial = random.choice(self.trialSet)
                    return self.currentTrial
                else:
                    #Failed, so repeat this trial
                    return self.currentTrial
                