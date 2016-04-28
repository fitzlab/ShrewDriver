from __future__ import division
import sys
sys.path.append("..")


from analysis.discrimination_analysis import *

class DiscriminationTrial:
    """One trial of a discrimination task."""

    def __init__(self, analysis=None):
        self.analysis = analysis  # type: DiscriminationAnalysis
        self.guaranteedSPlus = self.analysis.guaranteedSPlus
        self.sMinusPresentations = self.analysis.sMinusPresentations
        self.sMinusOrientations = self.analysis.sMinusOrientations
        self.sPlusOrientations = self.analysis.sPlusOrientations

        self.sMinusOrientation = -1
        self.sPlusOrientation = -1

        self.numSMinus = 0 #number of times SMINUS was presented

        self.trialStartTime = 0
        self.hint = False # type: bool, true if hint was dispensed
        self.reward = False  # type: bool, true if reward was dispensed
        self.totalmL = 0
        self.hintmL = 0
        self.trialNum = 0

        #results
        self.result = None
        self.resultState = None
        self.hint = True

        self.hintTime = None
        self.rewardTime = None

        self.stateHistory = []
        self.stateTimes = []
        self.actionHistory = []
        self.actionTimes = []

        self.lines = [] #stores logfile lines until trial is finished and ready to be analyzed

    def analyze(self):
        p = re.compile('\d+')

        # determine what orientations were used in this trial
        for line in self.lines:
            if re.search('ori', line) or re.search('sqr', line):
                toks = line.split()
                ori = toks[0][3:]

                if float(ori) in self.sMinusOrientations:
                    self.sMinusOrientation = float(ori)
                else:
                    self.sPlusOrientation = float(ori)

        # record events
        for line in self.lines:
            if re.search('RL', line):
                self.hint = True
                m = p.findall(line)
                self.hintTime = float(m[0] + '.' + m[1])
            elif re.search('RH', line):
                self.reward = True
                m = p.findall(line)
                self.rewardTime = float(m[0] + '.' + m[1])
            elif re.search('bolus', line):
                m = p.findall(line)
                bolusSize = float(m[0] + "." + m[1])
                self.totalmL += bolusSize
            elif re.search('user_reward', line):
                linesub = line[line.find('user_reward'):]
                m = p.findall(linesub)
                bolusSize = float(m[0] + "." + m[1])
                self.totalmL += bolusSize
                self.hintmL += bolusSize
            elif re.search('hint', line):
                m = p.findall(line)
                bolusSize = float(m[0] + "." + m[1])
                self.totalmL += bolusSize
                self.hintmL += bolusSize

            elif re.search('Lx', line):
                self.isLicking = True
                self.actionHistory.append(Actions.LICK)
                m = p.findall(line.split()[1])
                self.actionTimes.append(float(m[0] + '.' + m[1]))
            elif re.search('Lo', line):
                self.isLicking = False
                self.actionHistory.append(Actions.LICK_DONE)
                m = p.findall(line)
                self.actionTimes.append(float(m[0] + '.' + m[1]))

            elif re.search('Tx', line):
                self.actionHistory.append(Actions.TAP)
                m = p.findall(line.split()[1])
                self.actionTimes.append(float(m[0] + '.' + m[1]))
            elif re.search('To', line):
                self.actionHistory.append(Actions.TAP_DONE)
                m = p.findall(line)
                self.actionTimes.append(float(m[0] + '.' + m[1]))

            elif re.search('Io', line):
                self.actionHistory.append(Actions.LEAVE)
                m = p.findall(line)
                self.actionTimes.append(float(m[0] + '.' + m[1]))


        # examine what states occurred
        for line in self.lines:
            if re.search('State', line):
                m = p.findall(line)
                self.stateHistory.append(int(m[0]))
                self.stateTimes.append(float(m[1] + "." + m[2]))

                if self.stateHistory[-1] == States.DELAY:
                    self.trialStartTime = float(m[1] + "." + m[2])

                if self.stateHistory[-1] == States.SMINUS:
                    self.numSMinus += 1

                if len(self.stateHistory) < 3:
                    #Usually means task was assigned a fail state by user input
                    self.result = Results.TASK_FAIL
                    

                elif self.stateHistory[-1] == States.TIMEOUT:
                    #end of trial
                    #Figure out what the trial result was based on actions and states
                    prevState = self.stateHistory[-2]
                    prevStateStart = self.stateTimes[-2]
                    self.resultState = prevState

                    if self.reward:
                        #could be a HIT or CORRECT_REJECT.
                        if self.guaranteedSPlus == False:
                            #the only lick result with a reward is HIT
                            self.result = Results.HIT
                        elif self.guaranteedSPlus == True:
                            #could be an sMinus or sPlus trial, let's find out
                            if self.numSMinus == max(self.sMinusPresentations):
                                #S- trial, so CR
                                self.result = Results.CORRECT_REJECT
                            else:
                                #S+ trial, so hit
                                self.result = Results.HIT

                    else:
                        #no reward earned; could be an ABORT, FALSE_ALARM, TASK_FAIL, MISS, NO_RESPONSE, or CORRECT_REJECT.
                        if prevState == States.DELAY:
                            #shrew was already licking when delay state began, causing an instant fail
                            self.result = Results.TASK_FAIL

                        elif len(self.actionHistory) > 0 and self.actionHistory[-1] == Actions.LEAVE and self.actionTimes[-1] >= prevStateStart:
                            #final action was leaving, and it led to the timeout. Was an aborted trial.
                            self.result = Results.ABORT

                        elif len(self.actionHistory) > 0 and self.actionHistory[-1] == Actions.LICK and self.actionTimes[-1] >= prevStateStart:
                            #lick caused trial to end; could be FALSE_ALARM or TASK_FAIL.
                            if prevState == States.GRAY:
                                if self.numSMinus == 1 and min(self.sMinusPresentations) == 1:
                                    #it was during the memory delay on a template task. It's a task error.
                                    self.result = Results.TASK_FAIL
                                else:
                                    #Test grating was just presented; this is a false alarm.
                                    self.result = Results.FALSE_ALARM
                            else:
                                #licks in any other states are screwups
                                self.result = Results.TASK_FAIL
                        else:
                            #trial ended on its own, so it's a MISS, NO_RESPONSE, or CORRECT_REJECT.
                            if self.guaranteedSPlus == True and self.numSMinus == max(self.sMinusPresentations):
                                self.result = Results.NO_RESPONSE
                            elif self.guaranteedSPlus == False and prevState == States.GRAY:
                                self.result = Results.CORRECT_REJECT
                            else:
                                self.result = Results.MISS
