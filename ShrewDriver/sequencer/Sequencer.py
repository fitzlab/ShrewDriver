import sys
sys.path.append("../global")
from Constants import *

'''
This gives you different ways of ordering trials. 
You provide a set of trials and select the sequence type, and then call getNextTrial() over and over.
You need to tell getNextTrial() whether the current trial succeeded or not. 
Run this file to see an example.

Sequences:
    RANDOM - Each trial is chosen randomly from the set of possible trials. (sample with replacement)
    BLOCK - Each trial is presented once in random order. (sample without replacement)
    RANDOM_RETRY - Each trial is chosen randomly. If a trial is failed, keep retrying until success.
    BLOCK_RETRY - Each trial is presented once (random order). Unsuccessful trials are repeated until success.
    SEQUENTIAL - Each trial is presented once (in order).
    INTERVAL - A set of hard trials, then a set of easy trials, and so on.

Implementation:
This is vaguely a Strategy pattern.
The inheritance is really half-assed, but whatever, it works and it's reasonably organized.
'''

class Sequencer(object):
    def __init__(self):
        #unused
        pass
    
    def __init__(self, trialSet, sequenceType):
        #this is the init you actually want
        if sequenceType == Sequences.RANDOM:
            import SequencerRandom
            self.sequencer = SequencerRandom.SequencerRandom(trialSet)
        if sequenceType == Sequences.RANDOM_RETRY:
            import SequencerRandomRetry
            self.sequencer = SequencerRandomRetry.SequencerRandomRetry(trialSet)
        if sequenceType == Sequences.BLOCK:
            import SequencerBlock
            self.sequencer = SequencerBlock.SequencerBlock(trialSet)
        if sequenceType == Sequences.BLOCK_RETRY:
            import SequencerBlockRetry
            self.sequencer = SequencerBlockRetry.SequencerBlockRetry(trialSet)
        if sequenceType == Sequences.SEQUENTIAL:
            import SequencerSequential
            self.sequencer = SequencerSequential.SequencerSequential(trialSet)
        if sequenceType == Sequences.INTERVAL:
            import SequencerInterval
            self.sequencer = SequencerInterval.SequencerInterval(trialSet)
        if sequenceType == Sequences.INTERVAL_RETRY:
            import SequencerIntervalRetry
            self.sequencer = SequencerIntervalRetry.SequencerIntervalRetry(trialSet)
        if sequenceType == Sequences.SPLUS_FOR_REJECT:
            import SequencerSPlusForReject
            self.sequencer = SequencerSPlusForReject.SequencerSPlusForReject(trialSet)
        if sequenceType == Sequences.SPLUS_FOR_REJECT_RETRY:
            import SequencerSPlusForRejectRetry
            self.sequencer = SequencerSPlusForRejectRetry.SequencerSPlusForRejectRetry(trialSet)
        else:
            pass
    
    def getNextTrial(self, result):
        #next trial will depend on the result of the current trial
        return self.sequencer.getNextTrial(result)

if __name__ == '__main__':
    trialSet = [1,2,3,4]
    
    import random
    
    print "\n==================\nRandom trials"
    x = Sequencer(trialSet,Sequences.RANDOM)
    for i in range(0,20):
        print "  " + str(x.getNextTrial(Results.HIT))
    
    
    print "\n==================\nRandom Trials, repeat on failure"
    x = Sequencer(trialSet,Sequences.RANDOM_RETRY)
    for i in range(0,20):
        if random.choice([True, False]):
            print "Success! Next trial: " + str(x.getNextTrial(Results.HIT))
        else:
            print "Failure! Next trial: " + str(x.getNextTrial(Results.FALSE_ALARM))
    
    

    print "\n==================\nBlock Trials"
    x = Sequencer(trialSet,Sequences.BLOCK)
    for i in range(0,20):
        print "  " + str(x.getNextTrial(Results.HIT))
    
    
    print "\n==================\nBlock Trials, repeat on failure"
    x = Sequencer(trialSet,Sequences.BLOCK_RETRY)
    for i in range(0,20):
        if random.choice([True, False]):
            print "Success! Next trial: " + str(x.getNextTrial(Results.HIT))
        else:
            print "Failure! Next trial: " + str(x.getNextTrial(Results.FALSE_ALARM))
    
    
    print "\n==================\nSequential trials"
    x = Sequencer(trialSet,Sequences.RANDOM)
    for i in range(0,20):
        print "  " + str(x.getNextTrial(Results.HIT))
    

    print "\n==================\nInterval trials"
    x = Sequencer(trialSet,Sequences.INTERVAL)
    for i in range(0,60):
        print "  " + str(x.getNextTrial(Results.HIT))
    
    
    