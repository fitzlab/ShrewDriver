from __future__ import division
import re
import fileinput
import glob
import datetime
import sys

sys.path.append("..")
from util.enumeration import Enumeration
from util.cache_decorators import *
from task.task_constants import *

"""
Analyzes data.
Reads in the log and settings files.
Produces a set of trials.
"""


# This is for analyzing data, based on the raw log file and settings file.

class DiscriminationTrial:
    
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

            elif re.search('Lx', line):
                self.isLicking = True
                self.actionHistory.append(Actions.LICK)
                m = p.findall(line)
                self.actionTimes.append(float(m[0] + '.' + m[1]))
            elif re.search('Lo', line):
                self.isLicking = False
                self.actionHistory.append(Actions.LICK_DONE)
                m = p.findall(line)
                self.actionTimes.append(float(m[0] + '.' + m[1]))

            elif re.search('Tx', line):
                self.actionHistory.append(Actions.TAP)
                m = p.findall(line)
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

                if self.stateHistory[-1] == States.TIMEOUT:
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

class DiscriminationAnalysis:
    """
    Analyzes a single log file.
    Requires the corresponding settings file.
    Init will read in files, then you can use the get_performance functions to summarize results.
    """
    
    def __init__(self, logFile, settingsFile, notesFile):
        self.trials = []

        self.isLicking = False

        # settings / log parameters
        self.trainer = ""
        self.midSessionTime = ""
        self.dayOfWeek = ""
        self.hintsUsed = False
        self.guaranteedSPlus = False
        self.sequenceType = ""
        self.shrewName = ""
        self.notes = "" #contents of notes file, not including automated analysis

        #do reading of settings file
        self.read_settings_file(settingsFile)

        #process log file
        self.t = DiscriminationTrial(analysis=self) #make first trial
        self.read_log_file(logFile)

        #--- pull out some more metadata ---#
        
        #trainer name, if available
        if notesFile is not None:
            self.read_notes_file(notesFile)

        #shrew name and day of week
        m = re.match("(.*)_(.*)_(\\d+)_log.txt", logFile.split("\\")[-1])
        self.shrewName = m.group(1)
        dateStr = m.group(2)        
        (year, month, date) = dateStr.split("-")
        self.date = datetime.date(int(year),int(month),int(date))
        self.session = m.group(3)
        daysOfWeek = ["","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        self.dayOfWeek = daysOfWeek[self.date.isoweekday()]
                
        #get time of day at middle of training session, in hh:mm format
        if len(self.trials) > 0:
            t0 = self.trials[0]
            tN = self.trials[-1]
            if len(t0.stateTimes) > 0 and len(tN.stateTimes) > 0:
                tMid = (t0.stateTimes[0] + tN.stateTimes[0]) / 2
                dtMid = datetime.datetime.fromtimestamp(tMid)
                self.midSessionTime = str(dtMid.hour).zfill(2) + ":" + str(dtMid.minute).zfill(2)
        
        #organize results into summary data for nice plotting
        self.trial_stats()
    
    def read_notes_file(self, notesFile):
        if not os.path.isfile(notesFile):
            return

        fileinput.close() # Close any existing fileinput handles, just in case
        f = fileinput.input(notesFile)
        for line in f:
            if "Theo here!" in line or ": Theo" in line:
                self.trainer = "Theo"
            if "JWS" in line:
                self.trainer = "Joe"
            if "VH" in line or ": Val" in line or "Valerie" in line:
                self.trainer = "Valerie"
            if "CF" in line:
                self.trainer = "Connor"
            if "SF" in line:
                self.trainer = "Susan"
            if "Shrew:" in line or "===" in line:
                #indicates the beginning of automated analysis data; not needed in notes.
                fileinput.close()
                break
            self.notes += line

    def read_settings_file(self, settingsFile):
        """eat a settings file, and thereby gain its powers"""
        fileinput.close() # Close any existing fileinput handles, just in case
        for line in fileinput.input(settingsFile):
            toks = line.split(" ")

            if toks[0] == "hintChance":
                if float(toks[2]) == 0:
                    self.hintsUsed = False
                else:
                    self.hintsUsed = True
            
            if toks[0] == "guaranteedSPlus":
                if toks[2].rstrip() == "True":
                    self.guaranteedSPlus = True
                else:
                    self.guaranteedSPlus = False

            if toks[0] == "sMinusPresentations":
                exec("self." + line)

            if toks[0] == "sPlusOrientations":
                exec("self." + line)    

            if toks[0] == "sMinusOrientations":
                exec("self." + line)

            if toks[0] == "sPlusOrientation":
                self.sPlusOrientations = [float(toks[2])]

            if toks[0] == "sequenceType ":
                if "0" in toks[3]:
                    self.sequenceType = "RANDOM"
                if "1" in toks[3]:
                    self.sequenceType = "BLOCK"
                if "2" in toks[3]:
                    self.sequenceType = "RANDOM_RETRY"
                if "3" in toks[3]:
                    self.sequenceType = "BLOCK_RETRY"
                if "4" in toks[3]:
                    self.sequenceType = "SEQUENTIAL"
                if "5" in toks[3]:
                    self.sequenceType = "INTERVAL"
                if "6" in toks[3]:
                    self.sequenceType = "INTERVAL_RETRY"

            if toks[0] == "grayDuration":
                exec("self." + line)

            if toks[0] == "gratingDuration":
                exec("self." + line)

            if toks[0] == "rewardDuration":
                exec("self." + line)

            if toks[0] == "variableDelayMin":
                exec("self." + line)

            if toks[0] == "variableDelayMax":
                exec("self." + line)



    def read_log_file(self, logFile):
        """eat a log file, to absorb its knowledge"""
        fileinput.close() # Close any existing fileinput handles, just in case
        for line in fileinput.input(logFile):
            self.process_line(line)   

    def process_line(self, line):
        """Reads a single line of the log. If line represents a timeout state, trial is complete."""
        self.t.lines.append(line)
        if re.search('State0', line):
            self.t.analyze()
            self.trials.append(self.t)
            self.t = DiscriminationTrial(analysis=self)

    def trial_stats(self):
        """
        Call this after data processing to get statistics.
        Makes raw numbers easily accessible. 
        Percents will be rounded to the hundredths.
        """
        
        #inits
        self.nTrials = len(self.trials)
        self.taskErrors = 0
        self.taskErrorRate = 0

        self.discriminationPercent = 0

        self.sPlusResponses = 0
        self.sPlusTrials = 0
        self.sPlusResponseRate = 0

        self.sMinusRejects = 0
        self.sMinusTrials = 0
        self.sMinusRejectRate = 0

        self.totalmL = 0
        self.mLPerHour = 0
        self.trialsPerHour = 0
        self.trainingDuration = 0

        if self.nTrials == 0:
            return

        #counts of each result type
        self.resultCounts = {r: 0 for r in resultsSet}
        for t in self.trials:
            if t.result is None:
                continue
            self.resultCounts[Results.whatis(t.result)] += 1

            
        results = self.resultCounts #shorthand
        
        #Task error rate
        self.taskErrors = results["TASK_FAIL"]
        self.taskErrorRate = round(100* (self.taskErrors / self.nTrials), 2)
        
        #sPlus and sMinus correct counts
        self.sPlusResponses = results["HIT"]
        self.sPlusTrials = results["MISS"] + results["HIT"]
        if self.sPlusTrials > 0:
            self.sPlusResponseRate = round(100*(self.sPlusResponses / self.sPlusTrials), 2)
            
        self.sMinusRejects = results["CORRECT_REJECT"]
        self.sMinusTrials = results["CORRECT_REJECT"] + results["FALSE_ALARM"]
        if self.sMinusTrials > 0:
            self.sMinusRejectRate = round(100*(self.sMinusRejects / self.sMinusTrials), 2)
            
        #Discrimination percent
        self.discriminationPercent = round(0.5*self.sPlusResponseRate + 0.5*self.sMinusRejectRate, 2)

        #duration
        self.trainingDuration = (self.trials[-1].trialStartTime - self.trials[0].trialStartTime) / 60 / 60
        if self.trainingDuration > 0:
            self.trialsPerHour = len(self.trials) / self.trainingDuration
        else:
            self.trialsPerHour = 0

        #mL
        for t in self.trials:
            self.totalmL += t.totalmL

        if self.trainingDuration > 0:
            self.mLPerHour = self.totalmL / self.trainingDuration
        else:
            self.mLPerHour = 0



    #--- Display Functions ---#
    def str_overview(self):
        message = (
            "====" + "\n"
            "Shrew: " + self.shrewName + "\n" + "\n"
            'Success rate: ' + str(round(self.overallSuccessRate,2)) + '% (' + str(self.sPlusResponses+self.sMinusRejects) + '/' + str(self.nTrials) + ')' + "\n"
            '\nTotal Reward (mL): ' + str(self.session_mL) + "\n"
            "Run Time: " + self.runTime + "\n"
            "Reward Rate (mL/hour): " + str(self.rewardPerHour) + "\n"
            "\n"
        )
        return message

    def str_task_errors(self):
        message = (
            '====' + "\n"
            "TASK ERRORS\n" + "\n"
            "Task Error Rate: " + str(self.taskErrorRate) + "% (" + str(self.taskErrors) + "/" + str(self.nTrials) + ")" + "\n"

            '\nAborts: ' + str(self.abortCount) + "\n"
            '\nTask error details: \n'
        )
        for f in self.stateFailCounts:
            message += f + " " + str(self.stateFailCounts[f]) + "\n"
        message += "\n"
        return message

    def str_discrimination(self):
        nCorrect = self.sPlusResponses + self.sMinusRejects
        nDiscrimTrials = self.sPlusTrials + self.sMinusTrials
        message = (
            '====' + '\n'
            'DISCRIMINATION PERFORMANCE' + "\n"

            "\nOverall Discrimination: " + str(self.discriminationRate) + "%" + " (" + str(nCorrect) + "/" + str(nDiscrimTrials) + ")"
            #"\nOverall d': " + str(round(self.dPrimeOverall,3)) + "\n"

            "\nS+ Response Rate: " + str(self.sPlusResponseRate) + "% "
            "(" + str(self.sPlusResponses) + "/" + str(self.sPlusTrials) + ")"

            "\nS- Reject Rate: " + str(self.sMinusRejectRate) + "% "
            "(" + str(self.sMinusRejects) + "/" + str(self.sMinusTrials) + ")"
            "\n"
        )

        message += "\nS+ Response Rate by Orientation" + "\n"
        #sort dictionary keys
        sPlusOrientations = self.sPlusPerformances.keys()
        sMinusOrientations = self.sMinusPerformances.keys()

        sPlusOrientations = sorted(sPlusOrientations)
        sMinusOrientations = sorted(sMinusOrientations)

        for sPlusOrientation in sPlusOrientations:
            numCorrect = self.sPlusPerformances[sPlusOrientation].numCorrect
            numTrials = self.sPlusPerformances[sPlusOrientation].numTrials

            if numTrials == 0:
                continue

            successRate = numCorrect / numTrials * 100
            successRateStr = str(round(successRate,2))

            oriStr = str(sPlusOrientation) + " degrees:"
            oriStr += " " * (17-len(oriStr))
            oriStr += successRateStr + "% (" + str(numCorrect) + "/" + str(numTrials) + ")"
            oriStr += "\n"

            message += oriStr

        message += "\nS- Reject Rate by Orientation" + "\n"
        for sMinusOrientation in sMinusOrientations:
            numCorrect = self.sMinusPerformances[sMinusOrientation].numCorrect
            numTrials = self.sMinusPerformances[sMinusOrientation].numTrials

            if numTrials == 0:
                continue

            successRate = numCorrect / numTrials * 100
            successRateStr = str(round(successRate,2))

            oriStr = str(sMinusOrientation) + " degrees:"
            oriStr += " " * (17-len(oriStr))
            oriStr += successRateStr + "% (" + str(numCorrect) + "/" + str(numTrials) + ")"
            #oriStr += ", d'=" + str(round(self.sMinusPerformances[sMinusOrientation].dPrime,3))
            oriStr += "\n"
            message += oriStr

        message += "\n"
        return message






@CacheUnlessFilesChanged
def analyzeDir(dirPath):
    """
    Assumes the directory at dirPath contains sets of files including (logFile, settingsFile, notesFile).
    notesFiles are optional but nice.
    
    Returns a set of Analysis objects, one for each logFile.
    """
    
    os.chdir(baseDir)
    analyses = []

    for logFile in glob.glob("*log.txt"):

        settingsFile = re.match("(.*)log.txt", logFile).group(1) + "settings.txt"

        m = re.match("(.*)_(.*)_(\\d+)_log.txt", logFile)
        shrewName = m.group(1)
        dateStr = m.group(2)
        notesFile = dateStr + "-notes.txt"
        if not os.path.isfile(baseDir + "\\" + notesFile):
            #sometimes people forget the -notes, so try without that
            notesFile = dateStr + ".txt"
        if not os.path.isfile(baseDir + "\\" + notesFile):
            #sometimes it's _notes instead. Try that too.
            notesFile = dateStr + "_notes.txt"

        print "Log:", logFile, "\nSettings:", settingsFile, "\nNotes:", notesFile
        logFile = baseDir + "\\" + logFile
        settingsFile = baseDir + "\\" + settingsFile
        notesFile = baseDir + "\\" + notesFile

        if not os.path.isfile(settingsFile):
            continue
        
        a = DiscriminationAnalysis(logFile, settingsFile, notesFile)
        analyses.append(a)
        
    return analyses

if __name__ == "__main__":
    baseDir = r'C:\Users\theo\Desktop\chico\2014-10-21\0001'
    analyses = analyzeDir(baseDir)
    for a in analyses:  #type: Analysis
        print a.discriminationPercent
        print a.sPlusResponseRate
        print a.sMinusRejectRate
    