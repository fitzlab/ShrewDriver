from __future__ import division
import sys

sys.path.append("./util")
from Enumeration import *

sys.path.append("./global")
from Constants import *


# Contains all the info relevant to a trial, including results
# Used by trial sequencer for randomization, and by UI to display results
# Eventually this should be used by the log analyzer as well

class Trial():
    
    def __init__(self):
        self.sPlusOrientation = 0
        self.sMinusOrientation = 0
        self.numSMinus = 0 #number of times SMINUS is presented
        
        #results
        self.result = Results.SUCCESS
        self.resultState = States.REWARD
        self.hint = True
        self.totalMicroliters = 0
