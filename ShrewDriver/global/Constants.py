from __future__ import division
from Enumeration import Enumeration

#stores enums and values used in various places

'''
Sequences:
    RANDOM - Each trial is chosen randomly from the set of possible trials. (sample with replacement)
    BLOCK - Each trial is presented once (random order). 
    RANDOM_RETRY - Each trial is chosen randomly. If a trial is failed, keep retrying until success.
    BLOCK_RETRY - Each trial is presented once (random order). Unsuccessful trials are repeated until success.
'''

sequenceSet = ['RANDOM', 'BLOCK', 'RANDOM_RETRY', 'BLOCK_RETRY'] 
Sequences = Enumeration("Sequences", sequenceSet)


'''
Trial States:
    TIMEOUT - the black screen between trials. Longer timeout for failing, shorter for succeeding.
    WAITLICK - black screen until it has been a certain amount of time since the last lick.
    DELAY - gray screen of variable duration preceding the first grating presentation
    GRAY - gray screen between gratings, constant duration
    SPLUS - grating that is precedes rewardPeriod
    SMINUS - grating that does not precede rewardPeriod
    REWARD - gray screen during which reward is available. Same duration as GRAY.
'''

stateSet = ['TIMEOUT', 'WAITLICK', 'DELAY', 'GRAY', 'SPLUS', 'SMINUS', 'REWARD']
States = Enumeration("States", stateSet)



'''
Trial Results:
    SUCCESS - Correct lick
    FAIL - Incorrect lick
    ABORT - Shrew left IR beam
    NO_RESPONSE - Shrew didn't lick
'''
resultsSet = ['SUCCESS', 'FAIL', 'ABORT', 'NO_RESPONSE'] 
Results = Enumeration("Results", resultsSet)
