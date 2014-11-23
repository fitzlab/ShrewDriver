from __future__ import division
import sys

from TrialSequence import *


# Contains all the info relevant to a trial, including results
# Used during running by log analysis

class Trial():
    
    def __init__(self):
        self.sPlusOrientation = 0
        self.sMinusOrientation = 0
        self.sMinusPresentation = 0 #number of times SMINUS is presented
        

# Just double checking pass by reference properties here.
#if __name__ == '__main__':
#    trials = []
#    
#    finishedTrials = []
#    
#    for i in range(0,3):
#        t = Trial()
#        t.id = i
#        trials.append(t)
#    
#    finishedTrials.append(trials[1])
#    finishedTrials[0].finished = True
#    finishedTrials.append(trials[2])
#    finishedTrials[1].finished = True
#    
#    t = trials[1]
#    t.id = 666
#    
#    for i in range(0,3):
#        print str(trials[i].id) + " " + str(trials[i].finished)
