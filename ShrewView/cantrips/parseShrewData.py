import fileinput, re
import matplotlib.pyplot as plt

strPath = "C:/python-projects/ShrewView/2014-09-10_sensorData.txt"
f = open(strPath)

lickOnTimes = []
lickOffTimes = []

stimOnTimes = []
stimOffTimes = []

irOnTimes = []
irOffTimes = []

lowRewardTimes = []
highRewardTimes = []

lickTimeSinceStim = []
rewardsHighSinceStim = []

lastTenRewards = [0]*10
circIndex = 0
doAveraging = False
highRewardRates = []

lastStimOnset = 0

nRewards = 0
nRewardsLow = 0
nRewardsHigh = 0
stimIsOn = False

lastLickAt = 10000
lastLickBlockAt = 10000
lickBlockDelay = 500 #min time between licks to consider it a new block

timesLickBlockStartedBeforeRewardPeriod = 0
timesLickBlockStartedDuringRewardPeriod = 0

p = re.compile('\d+')
for line in fileinput.input(strPath):
    if re.search('Lx', line):
        m = p.findall(line)
        lickSinceStim = long(m[0]) - lastStimOnset
        timeSinceLastLick = long(m[0]) - lastLickAt
        if lickSinceStim < 4800 and timeSinceLastLick > lickBlockDelay:
            lickTimeSinceStim.append(lickSinceStim)
        lickOnTimes.append(long(m[0]))
        if timeSinceLastLick > lickBlockDelay:
            lastLickBlockAt = long(m[0])
            if lickSinceStim < 800:
                timesLickBlockStartedDuringRewardPeriod += 1
        lastLickAt = long(m[0])
    
    if re.search('Lo', line):
        m = p.findall(line)
        lickOffTimes.append(long(m[0]))
        
    if re.search('Sx', line):
        m = p.findall(line)
        stimOnTimes.append(long(m[0]))
        lastStimOnset = long(m[0])
        stimIsOn = True
        
        timeSinceLastLickBlock = long(m[0]) - lastLickBlockAt
        if timeSinceLastLickBlock < 800:
            timesLickBlockStartedBeforeRewardPeriod += 1
    
    if re.search('So', line):
        m = p.findall(line)
        stimOffTimes.append(long(m[0]))
        stimIsOn = False

    if re.search('RL', line):
        nRewardsLow += 1
        nRewards += 1
        lastTenRewards[circIndex] = 0
        circIndex = circIndex + 1
        
        
    if re.search('RH', line):
        rewardsHighSinceStim.append(long(m[0]) - lastStimOnset)
        nRewardsHigh += 1
        nRewards += 1
        lastTenRewards[circIndex] = 1
        circIndex = circIndex + 1
    
    if circIndex == 10:
        doAveraging = True
        circIndex = 0
    
    if doAveraging and (re.search('RL', line) or re.search('RH', line)):
        highRewardRates.append(float(sum(lastTenRewards)) / 10)
        

lickDurations = []
for i in range(0,len(lickOnTimes)):
    lickDurations.append(lickOffTimes[i] - lickOnTimes[i]);

lickTimeSinceStim.sort()
print lickTimeSinceStim

plt.hist(lickTimeSinceStim, 30)
plt.title('Licking starts at random times during the trial')
plt.xlabel('milliseconds since reward grating onset')
plt.show()

plt.hist(rewardsHighSinceStim, 5)
plt.title('Histogram\nTime (ms) of lick onset during reward grating')
plt.show()

print fileinput.lineno()

print "Low: ", str(nRewardsLow)
print "High: ", str(nRewardsHigh)
print "Percent: ", str(100*nRewardsHigh/(nRewardsLow+nRewardsHigh))
print "Chance: ", str((0.4/1.4)*100)

#plt.plot(range(0,len(highRewardRates)), highRewardRates)
#plt.title('% of rewards that were high');
#plt.show()

print 'licks started before reward: ' + str(timesLickBlockStartedBeforeRewardPeriod)
print 'licks started during reward: ' + str(timesLickBlockStartedDuringRewardPeriod)

print "DONE!"

print rewardsHighSinceStim