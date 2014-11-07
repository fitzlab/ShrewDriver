from __future__ import division
import fileinput, re

dirPath = "C:/Users/fitzlab1/Desktop/analysis/"

filePath = dirPath + "Chico_2014-10-21_1_log.txt"
filePath = dirPath + "Chico_2014-10-22_3_log.txt"
filePath = dirPath + "Chico_2014-10-23_1_log.txt"
filePath = dirPath + "Chico_2014-10-24_1_log.txt"
filePath = dirPath + "Chico_2014-10-27_1_log.txt"
filePath = dirPath + "Chico_2014-10-28_1_log.txt"
filePath = dirPath + "Chico_2014-11-04_3_log.txt"
filePath = dirPath + "Chico_2014-11-05_1_log.txt"
filePath = dirPath + "Chico_2014-11-06_2_log.txt"

#filePath = dirPath + "Mercury_2014-10-21_1_log.txt"
#filePath = dirPath + "Mercury_2014-10-22_1_log.txt"
#filePath = dirPath + "Mercury_2014-10-23_1_log.txt"
#filePath = dirPath + "Mercury_2014-10-24_1_log.txt"
#filePath = dirPath + "Mercury_2014-10-29_2_log.txt"
#filePath = dirPath + "Mercury_2014-10-31_1_log.txt"
#filePath = dirPath + "Mercury_2014-11-04_1_log.txt"
filePath = dirPath + "Mercury_2014-11-05_1_log.txt"
filePath = dirPath + "Mercury_2014-11-06_1_log.txt"

def concatType(type1, type2):
    return type1 + ' + ' + type2

def makeStateHistograms(stateLickTimes, grayScreenTypes):
    win = pg.GraphicsWindow()
    win.resize(800,800)
    win.setWindowTitle('Licks during each gray screen state')

    plots = []
    plots[0] = win.addPlot(row=1,col=1, title=grayScreenTypes[0])
    plots[1] = win.addPlot(row=1,col=2, title=grayScreenTypes[1]) 

    plots[2] = win.addPlot(row=2,col=1, title=grayScreenTypes[2])
    plots[3] = win.addPlot(row=3,col=1, title=grayScreenTypes[3])

    plots[4] = win.addPlot(row=2,col=2, title=grayScreenTypes[4])
    plots[5] = win.addPlot(row=3,col=2, title=grayScreenTypes[5])
    
    for i in range(0,len(grayScreenTypes)):
        t = 1
        if i==0: #DELAY
            t = 2
        y,x = np.histogram(stateLickTimes[grayScreenTypes[i]], bins=np.linspace(0, t, t/0.1))
        curve = pg.PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=(0, 0, 255, 80))
        plots[i].addItem(curve)

# These are the different things that can happen in a successful trial
hintTypes = ['Hint','No Hint']
distractorTypes = ['No Distractors', 'One Distractor', 'Two Distractors']

# set up results data structure 
successCounts = {}
for d in distractorTypes:
    for h in hintTypes:
        trialType = concatType(h, d)
        successCounts[trialType] = 0

# If it failed, let's find what state it failed at
stateSet = ['TIMEOUT', 'WAITLICK', 'DELAY', 'GRAY', 'SPLUS', 'SMINUS', 'REWARD']
failCounts = {}
for s in stateSet:
    failCounts[s] = 0

stateLickTimes = {} #for building histograms of lick times during each gray screen state
grayScreenTypes = ['DELAY', 'GRAY', 'REWARD_HINT', 'REWARD_NOHINT', 'D_REWARD_HINT', 'D_REWARD_NOHINT', ]
for s in grayScreenTypes:
    stateLickTimes[s] = []


abortCount = 0
noResponseCount = 0

prevState = '' #what state we were in, for labeling failure types
prevAction = '' #The last result-relevant thing the shrew did -- lick or leave.

wasSuccess = False
hint = False
numDistractors = 0

trialStartTime = 0
stateStartTime = 0


#Run through log file 
p = re.compile('\d+')
for line in fileinput.input(filePath):
    if re.search('State', line):
        m = p.findall(line)
        stateStartTime = float(m[1] + "." + m[2])
        if int(m[0]) == 0:
            if not wasSuccess:
                #this was a failure, abort, or no response, because 
                # we went to state 0 and it wasn't after a reward
                if prevAction == 'lick':
                    #failure
                    failCounts[prevState] += 1
                elif prevAction == 'leave':
                    #aborts
                    abortCount += 1
                else:
                    #no response
                    noResponseCount += 1
                    
            #new trial, so reset variables
            hint = False
            numDistractors = 0
            wasSuccess = False
            
        if stateSet[int(m[0])] == "SMINUS":
            numDistractors += 1
        
        prevAction = ''
        #record what state that was
        prevState = stateSet[int(m[0])]
        
    if re.search('RH', line):
        #Success! Record what kind of trial that was.
        trialType = ''
        distractorType = distractorTypes[numDistractors]
        if hint:
            trialType = concatType(hintTypes[0], distractorType)
        else:
            trialType = concatType(hintTypes[1], distractorType)
        successCounts[trialType] += 1
        wasSuccess = True
    if re.search('RL', line):
        hint = True
    if re.search('Io', line):
        prevAction = 'leave'
    if re.search('Lx', line):
        prevAction = 'lick'
        
        if prevState == "GRAY":# and not hint:
            m = p.findall(line)
            tTimeout = float(m[0] + "." + m[1])
            print str(tTimeout-stateStartTime)
            

completedTrials = 0

#each success type
numSuccesses = 0
print "===="
print "SUCCESSES:"
for key in successCounts.keys():
    print key + ' ' + str(successCounts[key])
    numSuccesses += successCounts[key]
print "Total Successes: " + str(numSuccesses)

#each failure type
numFailures = 0
print "===="
print "FAILURES:"
for key in stateSet:
    print key + ' ' + str(failCounts[key])
    numFailures += failCounts[key]
print "Total Failures: " + str(numFailures)

#completedTrials
print "===="
print "Total Trials With Responses: " + str(numFailures + numSuccesses)
print "Success rate: " + str(numSuccesses / (numFailures + numSuccesses) * 100) + "%"


#other types
print "===="
print 'Abort: ' + str(abortCount)
print 'No Response: ' + str(noResponseCount)
