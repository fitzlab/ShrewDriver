from __future__ import division
import sys
sys.path.append("..")

from sequencer.sequencer_base import Sequencer
import random
from constants.task_constants import *

# interval sequencing:
# Shrew gets a set of easy S- orientations, then a set of hard ones, and repeat.
# This takes a few calls to set up. First, call init(), then set numEasy, numHard, and tell it 
# what the easyOris and hardOris are. 

class SequencerIntervalRetry(Sequencer):
    
    def __init__(self, trialSet):
        self.trialSet = trialSet
        self.easyOris = []
        self.hardOris = []
        self.numEasy = 30
        self.numHard = 20
        self.trialBuffer = []
        self.trialBufferPos = 0
        
        self.trialsByOrientation = {}
        self.currentTrial = None
        
        for t in trialSet:
            ori = t.sMinusOrientation
            if not ori in self.trialsByOrientation.keys():
                self.trialsByOrientation[ori] = []
            self.trialsByOrientation[ori].append(t)

    def makeTrialBuffer(self):
        self.trialBuffer = []
        for i in range(0,self.numEasy):
            ori = random.choice(self.easyOris)
            t = random.choice(self.trialsByOrientation[ori])
            self.trialBuffer.append(t)
        
        for i in range(0, self.numHard):
            ori = random.choice(self.hardOris)
            t = random.choice(self.trialsByOrientation[ori])
            self.trialBuffer.append(t)
        
    def getNextTrial(self, trialResult):
        if trialResult == Results.HIT or trialResult == Results.CORRECT_REJECT or self.currentTrial == None:
            if self.trialBufferPos == len(self.trialBuffer):
                #randomize trial buffer and reset index
                self.makeTrialBuffer()
                self.trialBufferPos = 0             
                
            t = self.trialBuffer[self.trialBufferPos]
            self.trialBufferPos += 1
            self.currentTrial = t
            return t
        else:
            return self.currentTrial
        
