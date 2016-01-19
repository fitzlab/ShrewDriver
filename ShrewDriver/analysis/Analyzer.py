"""
Parses logfile data from a single session.
Makes summary statistics available.
Also used online during training.
Creates human-readable summaries of shrew performance.
"""

from __future__ import division

import os
import itertools
import glob
import re
import fileinput
import sys
import datetime

from collections import deque, namedtuple

sys.path.append("..")
from util.Enumeration import *

# For accumulating trial condition data
OrientationPair = namedtuple('OrientationPair', ['sMinus', 'sPlus'])
class OrientationPerformance():
    def __init__(self):
        self.numTrials = 0
        self.numCorrect = 0
        self.percentCorrect = 0

#yep
stateSet = ['TIMEOUT', 'INIT', 'DELAY', 'GRAY', 'SPLUS', 'SMINUS', 'REWARD']
States = Enumeration("States", stateSet)

actionSet = ['LICK','LEAVE']
Actions = Enumeration("Actions", actionSet)

resultsSet = ['HIT', 'CORRECT_REJECT', 'TASK_FAIL', 'MISS', 'NO_RESPONSE', 'ABORT', 'FALSE_ALARM'] 
Results = Enumeration("Results", resultsSet)

taskFailStates = ["DELAY", "SPLUS", "SMINUS", "GRAY"]

class OnlineAnalyzer():
    """
    Buffers events to be processed.
    At the end of each trial, process that trial's data and return a summary of the shrew's performance.
    Returns human-readable stats for online use.
    Also writes the stats to a text file, in case someone closes the online analysis window but needs the results.
    """

    def __init__(self, settingsFile, summaryFile):
        self.summaryFile = summaryFile
        self.eventsToProcess = deque()
        self.analyzer = Analyzer(settingsFile)

    def event(self, event):
        self.eventsToProcess.append(event)

    def process_events(self):
        """
        Process all the events in the deque. 
        Should be called at the end of each trial.
        Not threadsafe; expecting this to be used in-thread between trials.
        """
        while len(self.eventsToProcess) > 0:
            line = self.eventsToProcess.popleft()
            self.analyzer.process_line(line) 

        #compute stats
        self.analyzer.trial_stats()

        #get summary data 
        summary = self.analyzer.str_overview() + self.analyzer.str_discrimination() + self.analyzer.str_task_errors()

        #save summary data to backup file
        with open(self.summaryFile, 'w') as fh:
            fh.write(summary)

        return summary    

class Analyzer():
    """
    Analyzes log files containing shrew data.
    Requires a settings file, which tells us what kind of trial structure to expect.

    For online analysis, no logFile is needed.
    """

    def __init__(self, settingsFile, logFile=None):
        # initialize
        self.trials = []
        self.t = Trial()
        self.settingsFile = settingsFile
        self.logFile = logFile
        

        self.isLicking = False

        # settings / log parameters
        self.numSMinusPresentations = []
        self.trainer = ""
        self.midSessionTime = ""
        self.dayOfWeek = ""
        self.hintsUsed = False
        self.guaranteedSPlus = False
        self.sequenceType = ""
        self.shrewName = ""
        self.notes = "" #contents of notes file, not including automated analysis

        #--- pull out some more metadata ---#
    
        #do reading of log / settings files
        self.read_settings_file()
        self.get_stim_combinations()

        if logFile is not None:
            self.read_log_file(logFile)
            self.trial_stats()

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
            '\nLicks during incorrect states: ' + str(self.taskFailCount) + "\n"
        )
        for f in self.stateFailCounts:
            message += f + " " + str(self.stateFailCounts[f]) + "\n"
        message += "\n"
        return message
    
    def str_discrimination(self):
        message = (
            '====' + '\n'
            'DISCRIMINATION PERFORMANCE' + "\n"
            
            "\nOverall Discrimination: " + str(self.discriminationRate) + "%"
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
    

    def get_stim_combinations(self):
        #find all sets of (sMinus, sPlus) such that sMinus != sPlus
        allPairs = set(itertools.product(self.sMinusOrientations, self.sPlusOrientations))
        self.orientationPairs = []
        for (sMinus, sPlus) in allPairs: 
            if abs(float(sMinus) - float(sPlus)) < 0.01:
                continue
            self.orientationPairs.append(OrientationPair(sMinus,sPlus))
    

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

        self.discriminationRate = 0

        self.sPlusResponses = 0
        self.sPlusTrials = 0
        self.sPlusResponseRate = 0

        self.sMinusRejects = 0
        self.sMinusTrials = 0
        self.sMinusRejectRate = 0

        self.overallSuccessRate = 0

        if self.nTrials == 0:
            return

        #counts of each result type
        self.resultCounts = {r:0 for r in resultsSet}
        for t in self.trials:
            if t.result is None:
                continue
            self.resultCounts[Results.whatis(t.result)] += 1
            
        results = self.resultCounts #shorthand
        
        #Task errors
        self.abortCount = results["ABORT"]
        self.taskFailCount = results["TASK_FAIL"]
        self.taskErrors = results["TASK_FAIL"] + results["ABORT"]
        self.taskErrorRate = round(100* (self.taskErrors / self.nTrials), 2)

        self.stateFailCounts = dict(zip(taskFailStates, [0]*4))
        for t in self.trials:
            if t.result == Results.TASK_FAIL:
                self.stateFailCounts[States.whatis(t.stateHistory[-2])] += 1
        
        
        #sPlus and sMinus correct counts
        self.sPlusResponses = results["HIT"]
        self.sPlusTrials = results["MISS"] + results["HIT"]
        if self.sPlusTrials > 0:
            self.sPlusResponseRate = round(100*(self.sPlusResponses / self.sPlusTrials), 2)
            
        self.sMinusRejects = results["CORRECT_REJECT"]
        self.sMinusTrials = results["CORRECT_REJECT"] + results["FALSE_ALARM"]
        if self.sMinusTrials > 0:
            self.sMinusRejectRate = round(100*(self.sMinusRejects / self.sMinusTrials), 2)
            
        #overall success rate
        self.overallSuccessRate = round(100 * (self.sMinusRejects + self.sPlusResponses) / self.nTrials, 2)
        
        #Discrimination percent
        self.discriminationRate = round(0.5*self.sPlusResponseRate + 0.5*self.sMinusRejectRate, 2)
        
        #Reward and time info
        self.session_mL = 0
        for t in self.trials:
            self.session_mL += t.total_mL
        
        self.rewardPerHour = 0
        self.runTime = ""
        self.startTime = ""
        self.endTime = ""
        self.midSessionTime = ""
        
        if len(self.trials) > 1:
            t0 = self.trials[0]
            tN = self.trials[-1]
            if len(t0.stateTimes) > 0 and len(tN.stateTimes) > 0:
                tStart = t0.stateTimes[0]
                tEnd = tN.stateTimes[0]
                tMid = (tStart + tEnd) / 2

                hours = (tEnd-tStart)/60/60
                self.rewardPerHour = round(self.session_mL / hours, 2)
                
                dtStart = datetime.datetime.fromtimestamp(tStart)
                dtEnd = datetime.datetime.fromtimestamp(tEnd)
                dtMid = datetime.datetime.fromtimestamp(tMid)

                self.startTime = str(dtStart.hour).zfill(2) + ":" + str(dtStart.minute).zfill(2)
                self.endTime = str(dtEnd.hour).zfill(2) + ":" + str(dtEnd.minute).zfill(2)
                self.midSessionTime = str(dtMid.hour).zfill(2) + ":" + str(dtMid.minute).zfill(2)

                dt = dtEnd - dtStart
                self.runTime = re.sub("\.[^\.]*", "", str(dt))
                
        #Breakdown by orientation
        sPlusStrings = [str(float(o)) for o in self.sPlusOrientations]
        sMinusStrings = [str(float(o)) for o in self.sMinusOrientations]

        self.sPlusPerformances = dict(zip(sPlusStrings, [OrientationPerformance() for i in range(len(self.sPlusOrientations))]))
        self.sMinusPerformances = dict(zip(sMinusStrings, [OrientationPerformance() for i in range(len(self.sMinusOrientations))]))
        
        for t in self.trials:
            sPlusOri = str(t.sPlusOrientation)
            sMinusOri = str(t.sMinusOrientation)
            if t.numSMinus == max(self.sMinusPresentations) and len(self.sMinusPresentations) > 1:
                #it's an sMinus trial 
                if t.result == Results.CORRECT_REJECT:
                    self.sMinusPerformances[sMinusOri].numCorrect += 1
                    self.sMinusPerformances[sMinusOri].numTrials += 1
                elif t.result == Results.FALSE_ALARM:
                    self.sMinusPerformances[sMinusOri].numTrials += 1
            else:
                #it's an sPlus trial 
                if t.result == Results.HIT:
                    self.sPlusPerformances[sPlusOri].numCorrect += 1
                    self.sPlusPerformances[sPlusOri].numTrials += 1
                elif t.result == Results.MISS:
                    self.sPlusPerformances[sPlusOri].numTrials += 1
                    

    def read_settings_file(self):
        #parse settings file to figure out what we're doing
        if not os.path.isfile(self.settingsFile):
            print "Error: Can't find file \"" + self.settingsFile + "\""
            return False
        with open(self.settingsFile, "r") as fh:
            for line in fh:
                line = line.rstrip()
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

        #look at settings file name
        #get shrew name, date, and session number
        m = re.match("(\w+)_(.*)_(\\d+)_settings.txt", self.settingsFile.split(os.sep)[-1])
        print self.settingsFile.split(os.sep)[-1]
        self.shrewName = m.group(1)
        self.sessionNumber = int(m.group(3))
        

    def read_log_file(self, logFile):
        """
        Read data from a log file (offline analysis)
        """
        for line in fileinput.input(logFile):
            self.process_line(line)      
    
    def process_line(self, line):
        """Reads a single line of the log. Makes trials."""
        p = re.compile('\d+')
        if re.search('State', line):
            m = p.findall(line)
            self.t.stateHistory.append(int(m[0]))
            self.t.stateTimes.append(float(m[1] + "." + m[2]))            

            if self.t.stateHistory[-1] == States.DELAY:
                self.t.trialStartTime = float(m[1] + "." + m[2])

            if self.t.stateHistory[-1] == States.SMINUS:
                self.t.numSMinus += 1
                
            if self.t.stateHistory[-1] == States.TIMEOUT:
                #end of trial        
                #Figure out what the trial result was based on actions and states
                prevState = self.t.stateHistory[-2]
                prevStateStart = self.t.stateTimes[-2]
                self.t.resultState = prevState

                if len(self.t.actionHistory)==0:
                    self.t.result = Results.NO_RESPONSE

                #abort condition
                elif self.t.actionHistory[-1] == Actions.LEAVE and self.t.actionTimes[-1] >= prevStateStart:
                    self.t.result = Results.ABORT

                #lick caused trial to end
                elif self.t.actionHistory[-1] == Actions.LICK and self.t.actionTimes[-1] >= prevStateStart:
                    if prevState == States.REWARD:
                        #licks in reward states are good! But which kind of good?   
                        if self.guaranteedSPlus == False:
                            #the only lick result with a reward is HIT
                            self.t.result = Results.HIT
                        elif self.guaranteedSPlus == True:
                            #could be an sMinus or sPlus trial, let's find out
                            if self.t.numSMinus == max(self.sMinusPresentations):
                                #S- trial, so CR
                                self.t.result = Results.CORRECT_REJECT
                            else:
                                #S+ trial, so hit
                                self.t.result = Results.HIT
                    elif prevState == States.GRAY:
                        #licks in GRAY states could be false alarms
                        if self.t.numSMinus == 1 and min(self.sMinusPresentations) == 1:
                            #it was during the memory delay, so just a task error
                            self.t.result = Results.TASK_FAIL
                        else:
                            self.t.result = Results.FALSE_ALARM
                    else:
                        #licks in any other states are screwups
                        self.t.result = Results.TASK_FAIL

                elif self.isLicking and prevState == States.DELAY:
                    #already licking when delay comes up, instant fail
                    self.t.result = Results.TASK_FAIL

                elif prevState == States.REWARD:
                    #could be a miss or no_response
                    if self.guaranteedSPlus == True and self.t.numSMinus == max(self.sMinusPresentations):
                        self.t.result = Results.NO_RESPONSE
                    else:
                        self.t.result = Results.MISS
                elif prevState == States.GRAY and self.guaranteedSPlus == False:
                    self.t.result = Results.CORRECT_REJECT
                
                else:
                    print "Error in trial. Final state was: " + str(States.whatis(prevState))
                    
                self.trials.append(self.t)
                self.t = Trial()

        if re.search('ori', line) or re.search('sqr', line):
            toks = line.split()
            ori = toks[0][3:]
            
            if float(ori) in self.sMinusOrientations and self.t.sMinusOrientation == -1:
                self.t.sMinusOrientation = float(ori)
            else:
                self.t.sPlusOrientation = float(ori)
        
        #events
        if re.search('RL', line):
            self.t.hint = True
        elif re.search('Io', line):
            self.t.actionHistory.append(Actions.LEAVE)
            m = p.findall(line)
            self.t.actionTimes.append(float(m[0] + '.' + m[1]))
        elif re.search('Lx', line):
            self.isLicking = True
            self.t.actionHistory.append(Actions.LICK)
            m = p.findall(line)
            self.t.actionTimes.append(float(m[0] + '.' + m[1]))
        elif re.search('Lo', line):
            self.isLicking = False

        elif re.search('bolus', line):
            m = p.findall(line)
            bolusSize = float(m[0] + "." + m[1])
            self.t.total_mL += bolusSize   


class Trial:
    
    def __init__(self):
        self.sMinusOrientation = -1
        self.sPlusOrientation = -1
        
        self.numSMinus = 0 #number of times SMINUS was presented
    
        self.trialStartTime = 0
        self.hint = False #true if hint
        self.total_mL = 0
        self.trialNum = 0
    
        #results
        self.result = None
        self.resultState = None
        self.hint = True
    
        self.stateHistory = []
        self.stateTimes = []
        self.actionHistory = []
        self.actionTimes = []
    


def analyzeDir(baseDir):
    """
    Assumes the directory at dirPath contains sets of files including (logFile, settingsFile, notesFile).
    notesFiles are optional but nice.
    
    Returns a set of Analysis objects, one for each logFile.
    """
    
    analyses = []

    for logFile in glob.glob(baseDir + os.sep + "*log.txt"):

        settingsFile = re.match("(.*)log.txt", logFile).group(1) + "settings.txt"
        
        m = re.match("(.*)_(.*)_(\\d+)_log.txt", logFile)
        shrewName = m.group(1)
        dateStr = m.group(2)

        logFilePath = os.path.abspath(logFile)
        settingsFilePath = os.path.abspath(settingsFile)

        a = Analyzer(settingsFilePath, logFilePath)
        analyses.append(a)
        
    return analyses
    

def test():
    """
    Run the three test files, and print some data
    """
    testDir = r'C:\Users\fitzlab1\Desktop\butters analysis'#r".\test_logs"
    analyses = analyzeDir(testDir)
    
    for a in analyses:
        print a.str_overview() + a.str_discrimination() + a.str_task_errors()

if __name__ == "__main__":
    test()