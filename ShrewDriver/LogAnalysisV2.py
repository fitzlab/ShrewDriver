from __future__ import division
import fileinput, re, math

from util.Stats import dPrime, criterion

class Trial:
    trialStartTime = 0
    sMinusOri = -1 #degrees. -1 is a placeholder.
    sPlusOri = -1
    currentOri = -1 #holds ori information until we know if it's an SMINUS or an SPLUS
    hint = False #true if hint
    totalReward = 0
    trialNum = 0
    result = ''
    
    def __init__(self):
        self.stateHistory = []
        self.stateTimes = []
        self.actionHistory = []
        self.actionTimes = []

stateSet = ['TIMEOUT', 'INIT', 'DELAY', 'GRAY', 'SPLUS', 'SMINUS', 'REWARD']
resultsSet = ['SUCCESS', 'CORRECT_REJECT', 'TASK_FAIL', 'NO_RESPONSE', 'ABORT', 'FALSE_ALARM'] 

class Analyzer():

    def __init__(self, filePath="", shrew=""):
        self.trials = []
        self.t = Trial()
        self.trialNum = 1 
        
        self.shrew = shrew
        
        if filePath is not "":
            if filePath.lower().find("chico") > -1:
                self.shrew = "Chico"
            else:
                self.shrew = "Other"
            
            # we're doing offline processing
            for line in fileinput.input(filePath):
                self.processLine(line)
        
        #otherwise, this is online processing while the experiment's running! 
        #processLine is called as the program runs.
        
        
    def processLine(self,line):
        p = re.compile('\d+')
        if re.search('State', line):
            m = p.findall(line)
            self.t.stateHistory.append(int(m[0]))
            self.t.stateTimes.append(float(m[1] + "." + m[2]))
            
            if stateSet[self.t.stateHistory[-1]] == "DELAY":
                self.t.trialStartTime = float(m[1] + "." + m[2])
            
            if stateSet[self.t.stateHistory[-1]] == "SPLUS":
                self.t.sPlusOri = self.t.currentOri
                
            if stateSet[self.t.stateHistory[-1]] == "SMINUS":
                self.t.sMinusOri = self.t.currentOri
            
            if stateSet[self.t.stateHistory[-1]] == "TIMEOUT":
                #end of trial
                #Figure out what the trial result was based on actions and states
                prevState = self.t.stateHistory[-2]
                prevStateStart = self.t.stateTimes[-2]
                
                if len(self.t.actionTimes) == 0 or self.t.actionTimes[-1] < prevStateStart:
                    #shrew did nothing this trial, so must be CORRECT_REJECT or NO_RESPONSE
                    if stateSet[prevState] == "GRAY":
                        self.t.result = "CORRECT_REJECT"
                    elif stateSet[prevState] == "REWARD":
                        self.t.result = "NO_RESPONSE"
                    else:
                        print "Error in trial number " + str(self.trialNum)
                        print str(self.t.stateHistory)
                        print str(self.t.stateTimes)
                        print str(self.t.actionHistory)
                        print str(self.t.actionTimes)
                        print "\n"
                elif self.t.actionHistory[-1] == 'LEAVE' and self.t.actionTimes[-1] >= prevStateStart:
                    #Leaving caused the previous state to end, so this was an abort
                    self.t.result = "ABORT"
                elif self.t.actionHistory[-1] == 'LICK' and self.t.actionTimes[-1] >= prevStateStart:
                    #Licking caused state to end... but was it a good lick or a bad one?
                    if stateSet[prevState] == "REWARD":
                        self.t.result = "SUCCESS"
                    else:
                        if self.shrew.lower() == 'chico' and self.t.stateHistory.count(stateSet.index("GRAY")) == 2 and prevState == stateSet.index("GRAY"):
                            #Chico only false alarms for the second GRAY, not the first
                            self.t.result = "FALSE_ALARM"
                        elif self.shrew.lower() != 'chico' and prevState == stateSet.index("GRAY"):
                            #Anyone else false alarms by licking at GRAY
                            self.t.result = 'FALSE_ALARM'
                        else:
                            #If it wasn't a false alarm, it was just a general screwup
                            self.t.result = 'TASK_FAIL'
                else:
                    print "Error reading trial number " + str(self.trialNum)
                    print str(self.t.stateHistory)
                    print str(self.t.stateTimes)
                    print str(self.t.actionHistory)
                    print str(self.t.actionTimes)
                    print "\n"
                    
                #print self.t.result
                
                #new trial, so reset variables
                self.t.trialNum = self.trialNum
                self.trialNum += 1
                self.trials.append(self.t)
                self.t = Trial()
            
        elif re.search('ori', line) or re.search('sqr', line):
            toks = line.split()
            ori = toks[0][3:]
            self.t.currentOri = ori
        
        #events
        if re.search('RL', line):
            self.t.hint = True
        elif re.search('Io', line):
            self.t.actionHistory.append('LEAVE')
            m = p.findall(line)
            self.t.actionTimes.append(float(m[0] + '.' + m[1]))
        elif re.search('Lx', line):
            self.t.actionHistory.append('LICK')
            m = p.findall(line)
            self.t.actionTimes.append(float(m[0] + '.' + m[1]))
        
        elif re.search('bolus', line):
            m = p.findall(line)
            bolusSize = float(m[0] + "." + m[1])
            self.t.totalReward += bolusSize

    
    def summaryResults(self):
        abortCount = 0
        noResponseCount = 0
        correctRejectCount = 0
        taskFailCount = 0
        falseAlarmCount = 0
        successCount = 0
        totalReward = 0
        
        for t in self.trials:
            if t.result == 'ABORT':
                abortCount += 1
            if t.result == 'NO_RESPONSE':
                noResponseCount += 1
            if t.result == 'CORRECT_REJECT':
                correctRejectCount += 1
            if t.result == 'TASK_FAIL':
                taskFailCount += 1
            if t.result == 'FALSE_ALARM':
                falseAlarmCount += 1
            if t.result == 'SUCCESS':
                successCount += 1
            totalReward += t.totalReward
        
        print "===="
        print "SUMMARY\n"

        numTrials = len(self.trials)
        successRate = (successCount+correctRejectCount) / numTrials * 100
        
        print 'Success rate: ' + str(round(successRate,2)) + '% (' + str(successCount+correctRejectCount) + '/' + str(numTrials) + ')'
        
        runTimeSeconds = self.trials[-1].stateTimes[-1] - self.trials[0].stateTimes[0]
        rewardPerHour = round(totalReward / (runTimeSeconds/60/60),2)
        
        print 'Total Reward: ' + str(totalReward) + " mL (" + str(rewardPerHour) + " mL / hour)" 
        
        #runtime in human units
        runTimeHours = math.floor(runTimeSeconds/60/60)
        if runTimeHours >= 1:
            runTimeSeconds -= runTimeHours*60*60
        runTimeMinutes = math.floor(runTimeSeconds/60)
        if runTimeMinutes >= 1:
            runTimeSeconds -= runTimeMinutes*60
        
        timeStr = str(int(runTimeHours)).zfill(2) + ":"
        timeStr += str(int(runTimeMinutes)).zfill(2) + ":" + str(int(runTimeSeconds)).zfill(2)
        print "Run Time: " + timeStr
        
        return (round(successRate,2),rewardPerHour)
    
    def taskErrors(self):
        abortCount = 0
        taskFailCount = 0
        failsDelay = 0
        failsSPlus = 0
        failsSMinus = 0
        failsGray = 0
        
        for t in self.trials:
            if t.result == 'ABORT':
                abortCount += 1
            if t.result == 'TASK_FAIL':
                if t.stateHistory[-2] == stateSet.index("DELAY"):
                    failsDelay += 1
                if t.stateHistory[-2] == stateSet.index("SPLUS"):
                    failsSPlus += 1
                if t.stateHistory[-2] == stateSet.index("SMINUS"):
                    failsSMinus += 1
                if self.shrew.lower() == "chico" and t.stateHistory[-2] == stateSet.index("GRAY") and \
                t.stateHistory.count(stateSet.index("GRAY")) == 1:
                    failsGray += 1
        
        taskFailCount = failsDelay + failsSPlus + failsSMinus + failsGray
        
        taskErrors = abortCount + taskFailCount
        numTrials = len(self.trials)
        
        taskErrorRate = round(100*taskErrors/numTrials,2)
        
        print '===='
        print "TASK ERRORS\n"
        print "Task Error Rate: " + str(taskErrorRate) + "% (" + str(taskErrors) + "/" + str(numTrials) + ")"
        
        print '\nAborts: ' + str(abortCount)
        print '\nTask Fails: ' + str(taskFailCount)
        print "DELAY: " + str(failsDelay)
        print "SPLUS: " + str(failsSPlus)
        print "SMINUS: " + str(failsSMinus)
        if self.shrew.lower() == "chico":
            print "GRAY (first one only): " + str(failsGray)
        print '===='
        
        return taskErrorRate
          
    def discriminationPerformance(self):
        
        print 'DISCRIMINATION PERFORMANCE\n'
        
        oriTypesArray = []
        correctRejectsArray = []
        sMinusTrialCountsArray = []
        
        sMinusOrientations = []
        sPlusOrientations = []
        
        #find what S+ and S- orientations there are in the trial set
        grayStateNum = stateSet.index("GRAY")
        
        sPlusMisses = 0
        sPlusTrials = 0
        
        for t in self.trials:
            sPlus = t.sPlusOri
            sMinus = t.sMinusOri
            
            if sMinus != -1 and not sMinus in sMinusOrientations:
                sMinusOrientations.append(sMinus)
            if sPlus != -1 and not sPlus in sPlusOrientations:
                sPlusOrientations.append(sPlus)
            
            if t.result == "NO_RESPONSE":
                sPlusMisses += 1
            if stateSet.index("REWARD") in t.stateHistory:
                sPlusTrials += 1
            
        
        sMinusOrientations = [str(y) for y in sorted([float(x) for x in sMinusOrientations])]
        sPlusOrientations = [str(y) for y in sorted([float(x) for x in sPlusOrientations])]
        
        #print splus stuff
        if sPlusTrials == 0:
            return
        
        sPlusResponses = sPlusTrials - sPlusMisses
        sPlusResponseRate = round(sPlusResponses / sPlusTrials,2)
        print "S+ Response Rate: " + str(sPlusResponseRate * 100)  + "% (" + str(sPlusResponses) + "/" + str(sPlusTrials) + ")"
        
        #for each S-, find correct rejects
        for o in sMinusOrientations:
            oriCorrectReject = 0
            oriFalseAlarm = 0
            
            for t in self.trials:
                if str(float(t.sMinusOri)) == o:
                    
                    #Successes
                    if t.result == 'CORRECT_REJECT':
                        oriCorrectReject += 1
                    
                    if self.shrew.lower() == "chico" and stateSet.index("SPLUS") in t.stateHistory and t.stateHistory.count(grayStateNum) == 2:
                        #If Chico made it to the SPLUS after two GRAYs, he must have correctly rejected.
                        oriCorrectReject += 1
                    
                    #Fails
                    if t.result == 'FALSE_ALARM':
                        oriFalseAlarm += 1
            
            correctRejectsArray.append(oriCorrectReject)
            
            numSMinusTrials = oriCorrectReject + oriFalseAlarm
            sMinusTrialCountsArray.append(numSMinusTrials)
        
        totalCorrectRejects = sum(correctRejectsArray)
        totalSMinusTrials = sum(sMinusTrialCountsArray)

        if totalSMinusTrials > 0:
            correctRejectRate = totalCorrectRejects / totalSMinusTrials
            print "Correct Reject Rate: " + str(round(100 * correctRejectRate,2)) + "% (" + str(totalCorrectRejects) + "/" + str(totalSMinusTrials) +")"
        else:
            print "\nNo trials contained an S-.\n"
        
        print "d': " + str(dPrime(sPlusResponseRate, 1-correctRejectRate))
        
        print "\nCorrect Rejects by Orientation"
        for idx in range(0,len(sMinusOrientations)):
            oriCorrectReject = correctRejectsArray[idx]
            numSMinusTrials = sMinusTrialCountsArray[idx]
            
            if numSMinusTrials != 0:
                sMinusSuccessRate = oriCorrectReject / numSMinusTrials
                
                dPrimeOri = dPrime(sPlusResponseRate,1-sMinusSuccessRate)
                cOri = criterion(sPlusResponseRate,1-sMinusSuccessRate)
                
                oriStr = str(sMinusOrientations[idx]) + " degrees:"
                oriStr += " " * (17-len(oriStr))
                oriStr += str(round(sMinusSuccessRate * 100,2)) +"% (" + str(oriCorrectReject)
                oriStr += "/" + str(numSMinusTrials) + ")"
                oriStr += " " * (36-len(oriStr))
                oriStr += "d'=" + str(dPrimeOri) + "   "
                oriStr += "c=" + str(cOri) + ""
                print oriStr
        
        print "===="
        sMinusOrientationsF = [float(x) for x in sMinusOrientations]
        
        print 'Plot code:'
        print 'oris = ' + str(sMinusOrientationsF) + ';'
        print 'correctRejects = ' + str(correctRejectsArray) + ';'
        print 'trialCounts = ' + str(sMinusTrialCountsArray) + ';'
        print 'plot(oris,correctRejects./trialCounts*100,\'b\');'
        print 'hold on; plot(oris,correctRejects./trialCounts*100,\'bo\');'
        
        print 'xlim([' + str(round(min(sMinusOrientationsF))) + ',' + str(round(max(sMinusOrientationsF))) + ']);ylim([0,100]);'
        print '===='
        
        return sPlusResponseRate


#This is a bit of Matlab output that might come in handy someday.


if __name__ == '__main__':
    #do offline analysis
    taskErrorRates = []
    mLPerHours = []
    successRates = []
    sPlusResponseRates = []

    dirPath = "C:/Users/fitzlab1/Desktop/day/"
    import glob
    import os
    os.chdir(dirPath)
    for file in glob.glob("*.txt"):
        filePath = dirPath + file
        
        a = Analyzer(filePath)
        
        summary = a.summaryResults()
        errors = a.taskErrors()
        
        taskErrorRates.append(errors)
        
        mLPerHours.append(summary[1])
        successRates.append(summary[0])
        sPlusResponseRate = a.discriminationPerformance()
        
        sPlusResponseRates.append(sPlusResponseRate)
        
        print filePath + "\n\n\n\n\n"


    print "\nsplus response rate"
    print str(sPlusResponseRates)

    print "\nsuccess rates"
    print str(successRates)

    print "\ntask error rates"
    print str(taskErrorRates)

    print "\nmL per hour"
    print str(mLPerHours)

