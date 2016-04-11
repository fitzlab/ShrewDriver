"""Contains at least one function that defines a shrew's task and devices."""

import sys
sys.path.append("..")


class ChicoARC():
    
    def __init__(self):
        self.name = "Chico"
        self.ardSensorPort = "COM10"
        self.syringePort = "COM11"
        self.stimbotPort = "COM12"
        self.stimDevice = None
        self.cameraID = 5

        self.screenDist = 25
        
class ChicoUpstairs():
    
    def __init__(self):
        self.name = "Chico"
        self.ardSensorPort = "COM100"
        self.syringePort = "COM101"
        self.stimbotPort = None
        self.stimDevice = Psycho(windowed=False)
        self.cameraID = 5

        self.screenDist = 25


def chico_headfix():
    shrew = ChicoUpstairs()
    task = TaskHeadfix(shrew)
    
    #params
    params = ParamsHeadfix()
    params.reward_mL = 0.2
    task.params = params

    #screen commands 
    task.setUpStates()
    task.initMode = Task.INIT_AUTO

    #ready to go
    task.start(do_ui=True, do_camera=False, do_logging=True)

def chico_discrimination():
    print "Using settings for Chico!"
    self.sPlusOrientations = [135]
    self.sMinusOrientations = [180]
    self.sMinusPresentations = [0,1] #how many times to display the SMINUS
    self.guaranteedSPlus = True #is there always an SPLUS in the trial?
    self.sequenceType = Sequences.RANDOM
    self.initiation = Initiation.TAP

    self.timeoutFail = 10
    self.timeoutAbort = 10
    self.timeoutSuccess = 10
    self.timeoutNoResponse = 10
    self.timeoutCorrectReject = 10

    self.initTime = 1

    self.variableDelayMin = 1.0
    self.variableDelayMax = 1.75

    self.gratingDuration = 0.5
    self.grayDuration = 1
    self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!

    self.hintChance = 0.0 #chance of sending a low reward at the start of the reward period

    self.hintBolus = 0.03 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
    self.rewardBolus = 0.150
    self.rewardBolusHardTrial = 0.250

    #stimbot setup, including command strings for each state
    #note that grating states will have an extra command added later to specify orientation and phase.
    self.screenDistanceMillis = 25
    self.commandStrings[States.TIMEOUT] = 'ac pab px0 py0 sx12 sy12\n'
    self.commandStrings[States.INIT] = 'ac paw px0 py0 sx12 sy12\n'
    self.commandStrings[States.DELAY] = 'sx0 sy0\n'
    self.commandStrings[States.SMINUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
    self.commandStrings[States.GRAY] = 'sx0 sy0\n'
    self.commandStrings[States.SPLUS] = 'as sf0.25 tf0 jf0 ja0 px0 py0 sx999 sy999\n'
    self.commandStrings[States.REWARD] = 'sx0 sy0\n'

