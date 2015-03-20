from __future__ import division
import sys

sys.path.append("./util")
from Enumeration import *

sys.path.append("./global")
from Constants import *


# Contains all the info relevant to a trial, including results
# Used by trial sequencer for randomization, and by UI to display results
# Also used by the log analyzer

class Trial():
    
    def __init__(self):
        self.numSMinus = 0 #number of times SMINUS is presented
        
        self.trialStartTime = 0
        self.sMinusOrientation = '-1' #degrees. -1 is a placeholder.
        self.sPlusOrientation = '-1'
        self.currentOri = '-1' #holds ori information until we know if it's an SMINUS or an SPLUS
        self.hint = False #true if hint
        self.totalMicroliters = 0
        self.trialNum = 0
        
        #results
        self.result = Results.HIT
        self.resultState = States.REWARD
        self.hint = True
        
        self.stateHistory = []
        self.stateTimes = []
        self.actionHistory = []
        self.actionTimes = []
