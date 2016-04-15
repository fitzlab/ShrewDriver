from __future__ import division
import sys
sys.path.append("..")

import re
import fileinput
import glob
import datetime

from util.enumeration import Enumeration
from util.cache_decorators import *
from constants.task_constants import *
from trial.discrimination_trial import *
from util.human import secondsToHuman
from util.stats import dPrime, criterion

"""
Analyzes data.
Reads in the log and settings files.
Produces a set of trials.
"""

class OrientationPerformance():
    def __init__(self):
        """Used in tabulating performance for display"""
        self.numTrials = 0
        self.numCorrect = 0
        self.percentCorrect = 0

# This is for analyzing data, based on the raw log file and settings file.

class DiscriminationAnalysis:
    """
    Analyzes a single log file.
    Requires the corresponding settings file.
    Init will read in files, then you can use the get_performance functions to summarize results.
    """

    def __init__(self, logFile=None, settingsFile=None, notesFile=None):
        self.logFile = logFile
        self.settingsFile = settingsFile
        self.notesFile = notesFile

        self.trials = []
        self.isLicking = False

        # settings / log parameters
        self.trainer = ""
        self.midSessionTime = ""
        self.dayOfWeek = ""
        self.hintsUsed = False
        self.guaranteedSPlus = True
        self.sequenceType = ""
        self.shrewName = ""
        self.notes = "" #contents of notes file, not including automated analysis


        #do reading of settings file
        self.read_settings_file(settingsFile)

        #make first trial
        self.t = DiscriminationTrial(analysis=self)

        #If no logfile, this is a live session -- nothing more to do yet, just wait for process_line calls etc.
        if logFile is None:
            return

        #process log file
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

        m = re.match("(.*)_(.*)_(\\d+)_settings.txt", settingsFile.split("\\")[-1])
        self.shrewName = m.group(1)

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
        self.stateFailCounts = {}

        self.overallSuccessRate = 0

        self.discriminationPercent = 0
        self.dPrimeOverall = 0

        self.sPlusResponses = 0
        self.sPlusTrials = 0
        self.sPlusResponseRate = 0
        self.sPlusPerformances = {sPlusOri : OrientationPerformance() for sPlusOri in self.sPlusOrientations}  # todo

        self.sMinusRejects = 0
        self.sMinusTrials = 0
        self.sMinusRejectRate = 0
        self.sMinusPerformances = {sMinusOri : OrientationPerformance() for sMinusOri in self.sMinusOrientations}  # todo

        self.totalmL = 0
        self.hintmL = 0
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
        self.taskErrors = results["TASK_FAIL"] + results["NO_RESPONSE"] + results["ABORT"]
        self.taskErrorRate = round(100* (self.taskErrors / self.nTrials), 2)

        for t in self.trials:  # type: DiscriminationTrial
            if t.result == Results.TASK_FAIL:
                if States.whatis(t.resultState) in self.stateFailCounts:
                    self.stateFailCounts[States.whatis(t.resultState)] += 1
                else:
                    self.stateFailCounts[States.whatis(t.resultState)] = 1

        #sPlus and sMinus correct counts
        self.sPlusResponses = results["HIT"]
        self.sPlusTrials = results["MISS"] + results["HIT"]
        if self.sPlusTrials > 0:
            self.sPlusResponseRate = round(100*(self.sPlusResponses / self.sPlusTrials), 2)

        self.sMinusRejects = results["CORRECT_REJECT"]
        self.sMinusTrials = results["CORRECT_REJECT"] + results["FALSE_ALARM"]
        if self.sMinusTrials > 0:
            self.sMinusRejectRate = round(100*(self.sMinusRejects / self.sMinusTrials), 2)

        #breakdown by orientation
        for t in self.trials:
            sPlusOri = t.sPlusOrientation
            sMinusOri = t.sMinusOrientation
            if t.numSMinus == max(self.sMinusPresentations) and len(self.sMinusPresentations) > 1:
                #it's an sMinus trial
                if sMinusOri == -1:
                    continue
                if t.result == Results.CORRECT_REJECT:
                    self.sMinusPerformances[sMinusOri].numCorrect += 1
                    self.sMinusPerformances[sMinusOri].numTrials += 1
                elif t.result == Results.FALSE_ALARM:
                    self.sMinusPerformances[sMinusOri].numTrials += 1
            else:
                #it's an sPlus trial
                if sPlusOri == -1:
                    continue
                if t.result == Results.HIT:
                    self.sPlusPerformances[sPlusOri].numCorrect += 1
                    self.sPlusPerformances[sPlusOri].numTrials += 1
                elif t.result == Results.MISS:
                    self.sPlusPerformances[sPlusOri].numTrials += 1


        #Discrimination percent
        self.discriminationPercent = round(0.5*self.sPlusResponseRate + 0.5*self.sMinusRejectRate, 2)
        self.dPrimeOverall = dPrime(self.sPlusResponseRate/100, 1-self.sMinusRejectRate/100)

        # Success rate
        self.overallSuccessRate = 100 * (self.sPlusResponses + self.sMinusRejects) / self.nTrials

        #duration
        self.trainingDuration = (self.trials[-1].trialStartTime - self.trials[0].trialStartTime) / 60 / 60
        if self.trainingDuration > 0:
            self.trialsPerHour = len(self.trials) / self.trainingDuration
        else:
            self.trialsPerHour = 0

        #mL
        for t in self.trials:
            self.totalmL += t.totalmL
            self.hintmL += t.hintmL

        if self.trainingDuration > 0:
            self.mLPerHour = self.totalmL / self.trainingDuration
        else:
            self.mLPerHour = 0



    #--- Display Functions ---#
    def str_overview(self):
        trainTime = secondsToHuman(self.trainingDuration*60*60)
        message = (
            "====" + "\n"
            "Shrew: " + self.shrewName + "\n" + "\n"
            'Success rate: ' + str(round(self.overallSuccessRate, 2)) + '% (' + str(self.sPlusResponses+self.sMinusRejects) + '/' + str(self.nTrials) + ')' + "\n"
            '\nTotal Reward (mL): ' + str(self.totalmL) + "\n")

        if self.hintmL > 0:
            message += "Reward from Hints (mL): " + str(self.hintmL) + " (" + str(round(100*self.hintmL/self.totalmL)) + "% of total)\n"

        message += (
            "Run Time: " + str(trainTime) + "\n"
            "Reward Rate (mL/hour): " + str(round(self.mLPerHour, 2)) + "\n"
            "\n"
        )
        return message

    def str_discrimination(self):
        nCorrect = self.sPlusResponses + self.sMinusRejects
        nDiscrimTrials = self.sPlusTrials + self.sMinusTrials
        message = (
            '====' + '\n'
            'DISCRIMINATION PERFORMANCE' + "\n"

            "\nOverall Discrimination: " + str(self.discriminationPercent) + "%" + " (" + str(nCorrect) + "/" + str(nDiscrimTrials) + ")"
            "\nOverall d': " + str(round(self.dPrimeOverall,3)) + "\n"

            "\nS+ Response Rate: " + str(self.sPlusResponseRate) + "% "
            "(" + str(self.sPlusResponses) + "/" + str(self.sPlusTrials) + ")"

            "\nS- Reject Rate: " + str(self.sMinusRejectRate) + "% "
            "(" + str(self.sMinusRejects) + "/" + str(self.sMinusTrials) + ")"
            "\n"
        )

        message += "\nS+ Response Rate by Orientation" + "\n"

        for sPlusOrientation in sorted(set(self.sPlusOrientations)):
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
        for sMinusOrientation in sorted(set(self.sMinusOrientations)):
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

    def str_task_errors(self):
        message = (
            '====' + "\n"
            "TASK ERRORS\n" + "\n"
            "Task Error Rate: " + str(self.taskErrorRate) + "% (" + str(self.taskErrors) + "/" + str(self.nTrials) + ")" + "\n")

        if self.resultCounts["ABORT"] > 0:
            # Probably won't appear; aborts are impossible now that IR is gone.
            # Kept for analysis of historical data only.
            message += '\nAborts: ' + str(self.resultCounts["ABORT"]) + "\n"

        if len(self.stateFailCounts.keys()) > 0:
            message += '\nTask error details: \n'

        for f in self.stateFailCounts:
            message += f + " " + str(self.stateFailCounts[f]) + "\n"
        message += "\n"
        return message

    def get_results_str(self):
        self.trial_stats()
        return self.str_overview() + self.str_discrimination() + self.str_task_errors()




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
