from __future__ import division

import sys
sys.path.append("..")

from constants.task_constants import *

def load_parameters(task):
    print "Using settings for Carmen!"

    task.screenDist = 25

    task.sPlusOrientations = [90]
    task.sMinusOrientations = [135]
    task.sMinusPresentations = [0,1] #how many times to display the SMINUS
    task.guaranteedSPlus = True #is there always an SPLUS in the trial?
    task.sequenceType = Sequences.RANDOM_RETRY
    task.initiation = Initiation.TAP
    task.airPuffMode = AirPuff.NONE

    task.timeoutFail = 3
    task.timeoutAbort = 3
    task.timeoutSuccess = 3
    task.timeoutNoResponse = 3
    task.timeoutCorrectReject = 0

    task.initTime = 1

    task.variableDelayMin = 1.0
    task.variableDelayMax = 1.75

    task.gratingDuration = 0.5
    task.grayDuration = 1
    task.rewardPeriod = task.grayDuration #needs to be no longer than gray duration!

    task.hintChance = 0.0 #chance of sending a low reward at the start of the reward period

    task.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
    task.rewardBolus = 0.100
    task.rewardBolusHardTrial = 0.200

    #stimbot setup, including command strings for each state
    #note that grating states will have an extra command added later to specify orientation and phase.
    task.screenDistanceMillis = 120
    task.commandStrings[States.TIMEOUT] = 'ac pab px0 py0 sx12 sy12\n'
    task.commandStrings[States.INIT] = 'ac paw px0 py0 sx12 sy12\n'
    task.commandStrings[States.DELAY] = 'sx0 sy0\n'
    task.commandStrings[States.SMINUS] = 'acgf sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
    task.commandStrings[States.GRAY] = 'sx0 sy0\n'
    task.commandStrings[States.SPLUS] = 'acgf sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
    task.commandStrings[States.REWARD] = 'sx0 sy0\n'

    task.showInteractUI = True  # Enables the interact UI, used in headfixed training.
