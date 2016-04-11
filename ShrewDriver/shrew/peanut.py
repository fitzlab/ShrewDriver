

class PeanutARC():

    def __init__(self):
        pass

def splinter_headfix():
    print "Using settings for headfix acclimation!"
    self.rewardCooldown = 0.5 #If shrew has not licked for this many seconds, make reward available.
    self.rewardBolus = 0.1

def splinter_discrimination():
    print "Using settings for Peanut!"
    self.sPlusOrientations = [0]
    self.sMinusOrientations = [155] #180-155 = 25 degree difference.
    self.sMinusPresentations = [0,1] #how many times to display the SMINUS
    self.guaranteedSPlus = True #is there always an SPLUS in the trial?
    self.sequenceType = Sequences.RANDOM_RETRY
    self.initiation = Initiation.TAP

    self.timeoutFail = 10
    self.timeoutAbort = 10
    self.timeoutSuccess = 10
    self.timeoutNoResponse = 10
    self.timeoutCorrectReject = 0

    self.initTime = 1

    self.variableDelayMin = 1.0
    self.variableDelayMax = 1.75

    self.gratingDuration = 0.5
    self.grayDuration = 1
    self.rewardPeriod = self.grayDuration #needs to be no longer than gray duration!

    self.hintChance = 0.0 #chance of sending a low reward at the start of the reward period

    self.hintBolus = 0.05 #0.03 is a good amount; just enough that the shrew will notice it but not enough to be worth working for on its own.
    self.rewardBolus = 0.100
    self.rewardBolusHardTrial = 0.150

    #stimbot setup, including command strings for each state
    #note that grating states will have an extra command added later to specify orientation and phase.
    self.screenDistanceMillis = 120
    self.commandStrings[States.TIMEOUT] = 'ac pab px0 py0 sx12 sy12\n'
    self.commandStrings[States.INIT] = 'ac paw px0 py0 sx12 sy12\n'
    self.commandStrings[States.DELAY] = 'sx0 sy0\n'
    self.commandStrings[States.SMINUS] = 'acgf sf0.25 tf0 jf0 ja0 px35 py0 sx999 sy60\n'
    self.commandStrings[States.GRAY] = 'sx0 sy0\n'
    self.commandStrings[States.SPLUS] = 'acgf sf0.25 tf0 jf0 ja0 px35 py0 sx999 sy999\n'
    self.commandStrings[States.REWARD] = 'sx0 sy0\n'