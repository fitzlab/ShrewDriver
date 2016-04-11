from __future__ import division
import sys
sys.path.append("..")

from util.enumeration import *

#stores enums and values used in various places

STATE_TIMEOUT = "TIMEOUT"
STATE_INIT = "INIT"
STATE_DELAY = "DELAY"
STATE_GRAY = "GRAY"
STATE_SPLUS = "SPLUS"
STATE_SMINUS = "SMINUS"
STATE_REWARD = "REWARD"

stateSet = [STATE_TIMEOUT, STATE_INIT, STATE_DELAY, STATE_GRAY, STATE_SPLUS, STATE_SMINUS, STATE_REWARD]
States = Enumeration("States", stateSet)

'''
Sequences:
    RANDOM - Each trial is chosen randomly from the set of possible trials. (sample with replacement)
    BLOCK - Each trial is presented once (random order). 
    RANDOM_RETRY - Each trial is chosen randomly. If a trial is failed, keep retrying until success.
    BLOCK_RETRY - Each trial is presented once (random order). Unsuccessful trials are repeated until success.
    SEQUENTIAL - Each trial is presented once (in order).
    INTERVAL - A set of hard trials, then a set of easy trials, and so on. Requires some setup, see SequencerInterval.py.
    INTERVAL_RETRY - A set of hard trials, then a set of easy trials, and so on. Requires setup. Unsuccessful trials are repeated until success.
'''

sequenceSet = ['RANDOM', 'BLOCK', 'RANDOM_RETRY', 'BLOCK_RETRY','SEQUENTIAL','INTERVAL','INTERVAL_RETRY']
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
Trial Actions:
    LICK - Shrew licks (onset)
    LEAVE - Shrew exits infrared beam; no longer used
    TAP - Shrew activates tap sensor (onset
    LICK_DONE - Shrew finishes a lick (offset)
    TAP_DONE - Shrew releases tap bar (offset)
'''
actionSet = ['LICK', 'LEAVE', 'TAP', 'LICK_DONE', 'TAP_DONE']
Actions = Enumeration("Actions", actionSet)


'''
Trial Results:
    HIT - Correct lick
    CORRECT_REJECT - Not responding in a no-go trial
    TASK_FAIL - Lick when no reward is possible by task structure (e.g. during a grating)
    MISS - Didn't lick in a go trial
    NO_RESPONSE - Shrew didn't lick
    ABORT - Shrew left IR beam during trial
    FALSE_ALARM - Lick following an SMINUS
'''

resultsSet = ['HIT', 'CORRECT_REJECT', 'TASK_FAIL', 'MISS', 'NO_RESPONSE', 'ABORT', 'FALSE_ALARM']
Results = Enumeration("Results", resultsSet)


'''
Trial Initiation Modes:
    IR - Shrew enters infrared beam
    LICK - Lick during INIT period starts trial; licks during DELAY are ignored
    TAP - Tap sensor during INIT starts trial. Shrew can hold tap sensor constantly.
    TAP_ONSET - Tap sensor during INIT starts trial. Tap sensor must be released first.
'''
initSet = ['IR', 'LICK', 'TAP', 'TAP_ONSET']
Initiation = Enumeration("Initiation", initSet)
