from __future__ import division
import fileinput, re, math, sys, time

from util.Stats import dPrime, criterion

sys.path.append("./trial")
from Trial import Trial

sys.path.append("./global")
from Constants import *

sys.path.append("./util")
import Human


'''
Analyzer will read the raw experiment data and turn it into useful stats.
It can do this online (by calls to processLine() as data comes in), 
or offline via its readFile function. 
To aggregate multiple days of data, just call readFile() repeatedly.
'''

class OrientationPerformance():
    def __init__(self):
        #used in dictionaries where the key is S+ orientation
        self.sPlusOrientation = -1
        self.sMinusOrientation = -1
        self.numTrials = 0
        self.numCorrect = 0
        
        self.criterion = 0
        self.dPrime = 0

class Analyzer():

    def __init__(self, shrew=""):
        self.trials = []
        self.t = Trial()
        self.trialNum = 1 
        
        self.animalName = shrew
        
        
        # Recompute flag for lazy processing, changes when we get new data
        self.needToCalculate = False
        
        #---  All the computed stats... ---#
        
        #summary data
        self.abortCount = 0
        self.noResponseCount = 0
        self.successCount = 0
        self.correctRejectCount = 0
        self.taskFailCount = 0
        self.falseAlarmCount = 0
        self.totalReward = 0
        
        self.numTrials = 0
        self.successRate = 0
        self.runTimeSeconds = 0
        self.rewardPerHour = 0
        
        # task errors
        self.abortCount = 0
        self.taskFailCount = 0
        self.failsDelay = 0
        self.failsSPlus = 0
        self.failsSMinus = 0
        self.failsGray = 0
        
        # discrimination performance
        self.sPlusCorrect = 0
        self.sPlusTrials = 0
        self.sPlusCorrectRate = 0
        
        self.sMinusCorrect = 0
        self.sMinusTrials = 0     
        self.sMinusCorrectRate = 0
        
        self.discriminationPercent = 0
        self.dPrimeOverall = 0
    
        self.sPlusPerformances = {} #will be a dictionary of OrientationPerformance objects
        self.sMinusPerformances = {}
        self.sPlusBySMinusPerformances = {}
        
        #used in determining if this is a "retry" or not
        self.prevTrialSuccess = False
        
        #limit analysis to the first n trials in each file
        self.trialsLimit = 99999
        self.cancelRepeatTrials = False
        
    def readFile(self, filePath):
        #read all lines in the given file. For offline use.
        thisFileTrials = 0
        if filePath is not "":
            # we're doing offline processing
            for line in fileinput.input(filePath):
                if thisFileTrials < self.trialsLimit:
                    nTrialsCurrent = len(self.trials)
                    self.processLine(line)
                    if len(self.trials) > nTrialsCurrent:
                        thisFileTrials += 1
    
    def calcSummaryResults(self):
        #reset counts
        self.abortCount = 0
        self.noResponseCount = 0
        self.correctRejectCount = 0
        self.taskFailCount = 0
        self.falseAlarmCount = 0
        self.successCount = 0
        self.totalReward = 0

        for t in self.trials:
            if t.result == Results.ABORT:
                self.abortCount += 1
            if t.result == Results.NO_RESPONSE:
                self.noResponseCount += 1
            if t.result == Results.CORRECT_REJECT:
                self.correctRejectCount += 1
            if t.result == Results.TASK_FAIL:
                self.taskFailCount += 1
            if t.result == Results.FALSE_ALARM:
                self.falseAlarmCount += 1
            if t.result == Results.HIT:
                self.successCount += 1
            self.totalReward += t.totalMicroliters
        
        self.numTrials = len(self.trials)
        self.successRate = (self.successCount+self.correctRejectCount) / self.numTrials * 100
        self.runTimeSeconds = self.trials[-1].stateTimes[-1] - self.trials[0].stateTimes[0]
        self.rewardPerHour = round(self.totalReward / (self.runTimeSeconds/60/60),2)
    
    def getSummaryResults(self):
        self.recomputeIfNeeded()
        message = "====" + "\n"
        message += "SUMMARY\n" + "\n"
        message += 'Success rate: ' + str(round(self.successRate,2)) + '% (' + str(self.successCount+self.correctRejectCount) + '/' + str(self.numTrials) + ')' + "\n"
        message += '\nTotal Reward: ' + str(self.totalReward) + "\n"
        message += "Run Time: " + Human.secondsToHuman(self.runTimeSeconds) + "\n"
        message += "Reward Rate (mL/hour): " + str(self.rewardPerHour) + "\n"
        message += "\n"
        return message
    
    def calcTaskErrors(self):
        self.abortCount = 0
        self.failsDelay = 0
        self.failsSPlus = 0
        self.failsSMinus = 0
        self.failsGray = 0
        for t in self.trials:
            if t.result == Results.ABORT:
                self.abortCount += 1
            if t.result == Results.TASK_FAIL:
                if t.stateHistory[-2] == States.DELAY:
                    self.failsDelay += 1
                if t.stateHistory[-2] == States.SPLUS:
                    self.failsSPlus += 1
                if t.stateHistory[-2] == States.SMINUS:
                    self.failsSMinus += 1
                if self.animalName.lower() == "chico" and t.stateHistory[-2] == States.GRAY and \
                t.stateHistory.count(States.GRAY) == 0:
                    self.failsGray += 1
        
        self.taskFailCount = self.failsDelay + self.failsSPlus + self.failsSMinus + self.failsGray
        
        self.taskErrors = self.abortCount + self.taskFailCount
        self.numTrials = len(self.trials)
        
        self.taskErrorRate = round(100*self.taskErrors/self.numTrials,2)
        
    def getTaskErrors(self):
        self.recomputeIfNeeded()
        
        message = '====' + "\n"
        message += "TASK ERRORS\n" + "\n"
        message += "Task Error Rate: " + str(self.taskErrorRate) + "% (" + str(self.taskErrors) + "/" + str(self.numTrials) + ")" + "\n"
        
        message += '\nAborts: ' + str(self.abortCount) + "\n"
        message += '\nLicks during incorrect states: ' + str(self.taskFailCount) + "\n"
        message += "DELAY: " + str(self.failsDelay) + "\n"
        message += "SPLUS: " + str(self.failsSPlus) + "\n"
        message += "SMINUS: " + str(self.failsSMinus) + "\n"
        #if self.animalName.lower() == "chico":
            #message += "GRAY (first one only): " + str(self.failsGray) + "\n"
        message += "\n"
        return message
        
    
    def calcDiscriminationPerformance(self): 

        self.sPlusCorrect = 0
        self.sPlusTrials = 0
        self.sPlusCorrectRate = 0
        
        self.sMinusCorrect = 0
        self.sMinusTrials = 0     
        self.sMinusCorrectRate = 0

        self.sPlusPerformances = {} #will be a dictionary of OrientationPerformance objects
        self.sMinusPerformances = {}
        self.sPlusBySMinusPerformances = {}       
        
        #populate dictionaries of S+ and S- trial results
        for t in self.trials:
            
            if t.result != Results.ABORT:
                #OK, the shrew didn't screw up this trial
                #So this is a trial that contains something interesting for results analysis
                
                if self.animalName.lower() == 'chico':
                    #Chico's a bit harder to analyze since he's got multiple gratings
                    
                    if t.sMinusOrientation != '-1' and t.stateHistory.count(States.GRAY) == 1 and t.result != Results.TASK_FAIL:
                        #This trial contains two GRAY states, so it's an S- trial
                        #create dictionary entry if needed
                        if not t.sMinusOrientation in self.sMinusPerformances:
                            op = OrientationPerformance()
                            op.sMinusOrientation = t.sMinusOrientation
                            op.sPlusOrientation = t.sPlusOrientation
                            self.sMinusPerformances[t.sMinusOrientation] = op
                        
                        self.sMinusPerformances[t.sMinusOrientation].numTrials += 1
                        
                        if t.result == Results.CORRECT_REJECT:
                            self.sMinusPerformances[t.sMinusOrientation].numCorrect += 1
                    
                    if t.sPlusOrientation != '-1' and t.stateHistory.count(States.GRAY) == 0 and States.REWARD in t.stateHistory:
                        #It's an S+ trial
                        #create dictionary entry if needed
                        if not t.sPlusOrientation in self.sPlusPerformances:
                            op = OrientationPerformance()
                            op.sMinusOrientation = t.sMinusOrientation
                            op.sPlusOrientation = t.sPlusOrientation
                            self.sPlusPerformances[t.sPlusOrientation] = op
                        
                        #update entry with trial results
                        self.sPlusPerformances[t.sPlusOrientation].numTrials += 1
                        if t.result == Results.HIT:
                            self.sPlusPerformances[t.sPlusOrientation].numCorrect += 1
                        
                        # Testing this out...
                        #potentially interesting -- get S+ results by S- orientation as well.
                        #Looks like no real correlation here; leaving code in in case it shows up
                        #with more data or something.
                        #if not t.sMinusOrientation in self.sPlusBySMinusPerformances:
                            #op = OrientationPerformance()
                            #op.sMinusOrientation = t.sMinusOrientation
                            #op.sPlusOrientation = t.sPlusOrientation
                            #self.sPlusBySMinusPerformances[t.sMinusOrientation] = op
                        #self.sPlusBySMinusPerformances[t.sMinusOrientation].numTrials += 1
                        #if t.result == Results.HIT:
                            #self.sPlusBySMinusPerformances[t.sMinusOrientation].numCorrect += 1
                      
                else:
                    #It's simple go / no go, analysis is easy
                    
                    if t.sPlusOrientation != '-1' and t.result != Results.TASK_FAIL:
                        #create dictionary entry if needed
                        if not t.sPlusOrientation in self.sPlusPerformances:
                            op = OrientationPerformance()
                            op.sMinusOrientation = t.sMinusOrientation
                            op.sPlusOrientation = t.sPlusOrientation
                            self.sPlusPerformances[t.sPlusOrientation] = op
                        
                        #update entry with trial results
                        self.sPlusPerformances[t.sPlusOrientation].numTrials += 1
                        if t.result == Results.HIT:
                            self.sPlusPerformances[t.sPlusOrientation].numCorrect += 1
                        
                    if t.sMinusOrientation != '-1' and t.result != Results.TASK_FAIL:
                        #create dictionary entry if needed
                        if not t.sMinusOrientation in self.sMinusPerformances:
                            op = OrientationPerformance()
                            op.sMinusOrientation = t.sMinusOrientation
                            op.sPlusOrientation = t.sPlusOrientation
                            self.sMinusPerformances[t.sMinusOrientation] = op
                            
                        #update entry with trial results
                        self.sMinusPerformances[t.sMinusOrientation].numTrials += 1
                        if t.result == Results.CORRECT_REJECT:
                            self.sMinusPerformances[t.sMinusOrientation].numCorrect += 1
        
        #overall discrimination stats
        sPlusOrientations = self.sPlusPerformances.keys()
        for sPlus in sPlusOrientations:
            self.sPlusTrials += self.sPlusPerformances[sPlus].numTrials
            self.sPlusCorrect += self.sPlusPerformances[sPlus].numCorrect
            
        sMinusOrientations = self.sMinusPerformances.keys()
        for sMinus in sMinusOrientations:
            self.sMinusTrials += self.sMinusPerformances[sMinus].numTrials
            self.sMinusCorrect += self.sMinusPerformances[sMinus].numCorrect
            
        if self.sPlusTrials > 0:      
            self.sPlusCorrectRate = self.sPlusCorrect / self.sPlusTrials                    
        if self.sMinusTrials > 0:      
            self.sMinusCorrectRate = self.sMinusCorrect / self.sMinusTrials
        
        if (self.sPlusTrials + self.sMinusTrials) > 0:
            self.discriminationPercent = (self.sPlusCorrect + self.sMinusCorrect) / (self.sPlusTrials + self.sMinusTrials) * 100
        self.dPrimeOverall = dPrime(self.sPlusCorrectRate, 1-self.sMinusCorrectRate)
    
        #calculate d' for each S- orientation against all S+
        for sMinus in sMinusOrientations:
            oriFalseAlarmRate = 1 - (self.sMinusPerformances[sMinus].numCorrect / self.sMinusPerformances[sMinus].numTrials)
            self.sMinusPerformances[sMinus].dPrime = dPrime(self.sPlusCorrectRate, oriFalseAlarmRate)
        
    
    def getDiscriminationPerformance(self):
        self.recomputeIfNeeded()
        
        message = '====' + '\n'
        message += 'DISCRIMINATION PERFORMANCE' + "\n"

        message += "\nOverall Discrimination: " + str(round(self.discriminationPercent,2)) + "%"
        message += "\nOverall d': " + str(round(self.dPrimeOverall,3)) + "\n"    

        message += "\nS+ Response Rate: " + str(round(self.sPlusCorrectRate*100, 2)) 
        message += "% (" + str(self.sPlusCorrect) + "/" + str(self.sPlusTrials) + ")"
        
        message += "\nS- Reject Rate: " + str(round(self.sMinusCorrectRate*100, 2)) 
        message += "% (" + str(self.sMinusCorrect) + "/" + str(self.sMinusTrials) + ")"

        message += "\n"
        
        #sort dictionary keys
        sPlusOrientations = self.sPlusPerformances.keys()
        sMinusOrientations = self.sMinusPerformances.keys()
        
        sPlusOrientations = [str(k) for k in sorted([float(y) for y in sPlusOrientations])]
        sMinusOrientations = [str(k) for k in sorted([float(y) for y in sMinusOrientations])]
        
        message += "\nS+ Response Rate by Orientation" + "\n"
        for sPlusOrientation in sPlusOrientations:
            numCorrect = self.sPlusPerformances[sPlusOrientation].numCorrect
            numTrials = self.sPlusPerformances[sPlusOrientation].numTrials
            
            successRate = numCorrect / numTrials * 100
            successRateStr = str(round(successRate,2))
            
            oriStr = str(sPlusOrientation) + " degrees:"
            oriStr += " " * (17-len(oriStr))
            oriStr += successRateStr + "% (" + str(numCorrect) + "/" + str(numTrials) + ")"
            message += oriStr + "\n"
        
        
        message += "\nS- Reject Rate by Orientation" + "\n"
        for sMinusOrientation in sMinusOrientations:
            numCorrect = self.sMinusPerformances[sMinusOrientation].numCorrect
            numTrials = self.sMinusPerformances[sMinusOrientation].numTrials
            
            successRate = numCorrect / numTrials * 100
            successRateStr = str(round(successRate,2))
            
            oriStr = str(sMinusOrientation) + " degrees:"
            oriStr += " " * (17-len(oriStr))
            oriStr += successRateStr + "% (" + str(numCorrect) + "/" + str(numTrials) + ")"
            oriStr += ", d'=" + str(round(self.sMinusPerformances[sMinusOrientation].dPrime,3))
            message += oriStr + "\n"
        
        #if self.animalName.lower() == 'chico':
            #message += "\nS+ Response Rate by S- Orientation" + "\n"
            #for sMinusOrientation in sMinusOrientations:
                #numCorrect = self.sPlusBySMinusPerformances[sMinusOrientation].numCorrect
                #numTrials = self.sPlusBySMinusPerformances[sMinusOrientation].numTrials
                
                #successRate = numCorrect / numTrials * 100
                #successRateStr = str(round(successRate,2))
                
                #oriStr = str(sMinusOrientation) + " degrees:"
                #oriStr += " " * (17-len(oriStr))
                #oriStr += successRateStr + "% (" + str(numCorrect) + "/" + str(numTrials) + ")"
                #message += oriStr + "\n"
                
        message += "\n"                   
        return message
    
    def getLastNTrials(self, nTrials):        
        trialsToReturn = []
        for i in range(len(self.trials)-1, -1, -1):
            t = self.trials[i]
            trialsToReturn.append(t)
        return trialsToReturn
    
    def recomputeIfNeeded(self):
        if self.needToCalculate:
            self.calcSummaryResults()
            self.calcTaskErrors()
            self.calcDiscriminationPerformance()
            self.needToCalculate = False
    
    def getLiveSummary(self):
        self.recomputeIfNeeded()
        message = self.getSummaryResults()
        message += self.getDiscriminationPerformance()
        message += self.getTaskErrors()
        return message
    
    def endOfTrial(self):
        #called by processLine whenever a trial is completed
        #Figure out what the trial result was based on actions and states
        prevState = self.t.stateHistory[-2]
        prevStateStart = self.t.stateTimes[-2]
        
        if len(self.t.actionTimes) == 0 or self.t.actionTimes[-1] < prevStateStart:
            #shrew did nothing this trial, so must be CORRECT_REJECT or NO_RESPONSE
            if prevState == States.GRAY:
                self.t.result = Results.CORRECT_REJECT
            elif prevState == States.REWARD:
                self.t.result = Results.NO_RESPONSE
            elif len(self.t.actionTimes) >= 3 and (self.t.stateTimes[-1] - self.t.stateTimes[-2]) < 0.1:
                if self.t.actionHistory[-1] == Actions.LEAVE:
                    self.t.result = Results.ABORT
                else:
                    #Went straight from DELAY into an S+ / S- and the shrew was in mid-lick at the time, causing an immediate fail.
                    #Quite rare but it happens.
                    self.t.result = Results.TASK_FAIL
            else:  
                print "Error in trial number " + str(self.trialNum)
                print str(self.t.stateHistory)
                print str(self.t.stateTimes)
                print str(self.t.actionHistory)
                print str(self.t.actionTimes)
                print "\n"        
        
             
        elif self.t.actionHistory[-1] == Actions.LEAVE and self.t.actionTimes[-1] >= prevStateStart:
            #Leaving caused the previous state to end, so this was an abort
            self.t.result = Results.ABORT
            
        elif self.t.actionHistory[-1] == Actions.LICK and self.t.actionTimes[-1] >= prevStateStart:
            #Licking caused state to end... but was it a good lick or a bad one?
            if self.animalName.lower() == 'chico':
                if prevState == States.REWARD:
                    if self.t.stateHistory.count(States.GRAY) == 1:
                        self.t.result = Results.CORRECT_REJECT
                    else:
                        self.t.result = Results.HIT                
                elif prevState == States.GRAY and self.t.stateHistory.count(States.GRAY) == 1:
                    self.t.result = Results.FALSE_ALARM
                else:
                    #If it wasn't a false alarm, it was just a general screwup
                    self.t.result = Results.TASK_FAIL
            else:
                #any non-chico animal
                if prevState == States.REWARD:
                    self.t.result = Results.HIT
                elif prevState == States.GRAY:
                    #Anyone else false alarms by licking at GRAY
                    self.t.result = Results.FALSE_ALARM
                else:
                    self.t.result = Results.TASK_FAIL
                    
        else:
            print "Error reading trial number " + str(self.trialNum)
            print str(self.t.stateHistory)
            print str(self.t.stateTimes)
            print str(self.t.actionHistory)
            print str(self.t.actionTimes)
            print "\n"
            
        #Retry: We only want to analyze the very first instance of each trial, repeats should be skipped
        if self.trialNum == 1 or self.prevTrialSuccess or not self.cancelRepeatTrials:
            self.trialNum += 1
            self.trials.append(self.t)
        
        #now determine if the current trial was a success for next time
        finalState = self.t.stateHistory[-2]
        result = self.t.result      
        
        if result == Results.HIT or result == Results.CORRECT_REJECT:
            self.prevTrialSuccess = True
        else:
            self.prevTrialSuccess = False  
        
        #new trial, so reset variables 
        endState = self.t.stateHistory[-1]
        endStateStart = self.t.stateTimes[-1]
        self.t = Trial()
        self.t.trialNum = self.trialNum   
        self.t.stateHistory.append(endState) #the end of the last trial is the beginning of this one
        self.t.stateTimes.append(endStateStart)
    
    def processLine(self,line):
        self.needToCalculate = True
        p = re.compile('\d+')
        if re.search('State', line):
            m = p.findall(line)
            self.t.stateHistory.append(int(m[0]))
            self.t.stateTimes.append(float(m[1] + "." + m[2]))
            
            if self.t.stateHistory[-1] == States.DELAY:
                self.t.trialStartTime = float(m[1] + "." + m[2])

            if self.t.stateHistory[-1] == States.SPLUS:
                self.t.sPlusOrientation = self.t.currentOri
                
            if self.t.stateHistory[-1] == States.SMINUS:
                self.t.sMinusOrientation = self.t.currentOri                  
            
            if self.t.stateHistory[-1] == States.TIMEOUT:
                self.endOfTrial()
                 
            if len(self.trials) > 0 and self.t.stateHistory[-1] == States.INIT and self.t.stateHistory[-2] != States.TIMEOUT:
                #After the first trial, if it goes to init without a timeout, it was a correct reject.
                self.endOfTrial()
            
        if re.search('ori', line) or re.search('sqr', line):
            toks = line.split()
            ori = toks[0][3:]
            self.t.currentOri = str(float(ori))
            
            if self.t.stateHistory[-1] == States.SPLUS:
                self.t.sPlusOrientation = self.t.currentOri
                
            if self.t.stateHistory[-1] == States.SMINUS:
                self.t.sMinusOrientation = self.t.currentOri            
        
        #events
        if re.search('RL', line):
            self.t.hint = True
        elif re.search('Io', line):
            self.t.actionHistory.append(Actions.LEAVE)
            m = p.findall(line)
            self.t.actionTimes.append(float(m[0] + '.' + m[1]))
        elif re.search('Lx', line):
            self.t.actionHistory.append(Actions.LICK)
            m = p.findall(line)
            self.t.actionTimes.append(float(m[0] + '.' + m[1]))
            
            #Measure lick time since S+ presentation
            #lickTime = float(m[0] + '.' + m[1])
            #lickTimeSinceSPlus = 0
            #if States.SPLUS in self.t.stateHistory:
                #for x in range(len(self.t.stateHistory)-1, -1, -1):
                    #if self.t.stateHistory[x] == States.SPLUS:
                        #sPlusTime = self.t.stateTimes[x]
                        #lickTimeSinceSPlus = lickTime - sPlusTime
                        #break
            #if lickTimeSinceSPlus != 0:
                #print str(lickTimeSinceSPlus)
            
        elif re.search('bolus', line):
            m = p.findall(line)
            bolusSize = float(m[0] + "." + m[1])
            self.t.totalMicroliters += bolusSize
    