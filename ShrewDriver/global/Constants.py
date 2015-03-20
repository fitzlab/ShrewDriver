from __future__ import division
from Enumeration import Enumeration

#stores enums and values used in various places

'''
Task types:
    TWOAFC - Two-alternative forced choice. 
    GNG - Go / No Go. 
    GNG_SPLUS - Go / No Go, but with an SPLUS following every correct rejection.
    NOSTIM - Task that doesn't use the screen, e.g. for acclimation to initiations or headfix.
'''

taskTypeSet = ['TWOAFC', 'GNG', 'GNG_SPLUS', 'NOSTIM']
TaskTypes = Enumeration("TaskTypes", taskTypeSet)

'''
Sequences:
    RANDOM - Each trial is chosen randomly from the set of possible trials. (sample with replacement)
    BLOCK - Each trial is presented once (random order). 
    RANDOM_RETRY - Each trial is chosen randomly. If a trial is failed, keep retrying until success.
    BLOCK_RETRY - Each trial is presented once (random order). Unsuccessful trials are repeated until success.
    SEQUENTIAL - Each trial is presented once (in order).
'''

sequenceSet = ['RANDOM', 'BLOCK', 'RANDOM_RETRY', 'BLOCK_RETRY','SEQUENTIAL'] 
Sequences = Enumeration("Sequences", sequenceSet)



'''
Trial States:
    TIMEOUT - the black screen between trials. Longer timeout for failing, shorter for succeeding.
    INIT - Trial initiation phase. See "Trial Initiation Modes" below.
    DELAY - gray screen of variable duration preceding the first grating presentation
    GRAY - gray screen between gratings, constant duration
    SPLUS - grating that is precedes rewardPeriod
    SMINUS - grating that does not precede rewardPeriod
    REWARD - gray screen during which reward is available. Same duration as GRAY.
'''

stateSet = ['TIMEOUT', 'INIT', 'DELAY', 'GRAY', 'SPLUS', 'SMINUS', 'REWARD']
States = Enumeration("States", stateSet)



'''
Trial Initiation Modes:
    LICK - Shrew licks (onset)
    LEAVE - Shrew exits infrared beam
'''
actionSet = ['LICK','LEAVE']
Actions = Enumeration("Actions", actionSet)

'''
Trial Results:
    HIT - Correct lick
    CORRECT_REJECT - Not responding in a no-go trial
    TASK_FAIL - Lick when no reward is possible by task structure (e.g. during a grating)
    NO_RESPONSE - Shrew didn't lick
    ABORT - Shrew left IR beam during trial
    FALSE_ALARM - Lick following an SMINUS
'''
resultsSet = ['HIT', 'CORRECT_REJECT', 'TASK_FAIL', 'NO_RESPONSE', 'ABORT', 'FALSE_ALARM'] 
Results = Enumeration("Results", resultsSet)

'''
Trial Initiation Modes:
    IR - Shrew enters infrared beam
    LICK - Lick during INIT period starts trial; licks during DELAY are ignored
    TAP - Tap sensor during INIT starts trial
'''
initSet = ['IR','LICK','TAP']
Initiation = Enumeration("Initiation", initSet)