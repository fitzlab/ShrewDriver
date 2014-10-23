import fileinput, re

dirPath = "C:/Users/theo/Desktop/analysis/"
filePath = dirPath + "Chico_2014-10-22_3_log.txt"
filePath = dirPath + "Mercury_2014-10-22_1_log.txt"

def concatType(type1, type2):
    return type1 + ' + ' + type2

# These are the different things that can happen in a successful trial
hintTypes = ['Hint','No Hint']
distractorTypes = ['No Distractors', 'One Distractor']

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

abortCount = 0
noResponseCount = 0

prevState = '' #what state we were in, for labeling failure types
prevAction = '' #The last result-relevant thing the shrew did -- lick or leave.

wasSuccess = False
hint = False
numDistractors = 0

trialStartTime = 0
stateStartTime = 0

p = re.compile('\d+')
for line in fileinput.input(filePath):
    if re.search('State', line):
        m = p.findall(line)
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



#other types
print "===="
print 'Abort: ' + str(abortCount)
print 'No Response: ' + str(noResponseCount)
