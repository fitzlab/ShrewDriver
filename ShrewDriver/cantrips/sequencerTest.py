import sys
sys.path.append("./sequencer")

from Constants import *
from Sequencer import *

trialSet = [1,2,3,4]

s = Sequencer(trialSet, Sequences.RANDOM)
s.getNextTrial()
print "BUTTS"