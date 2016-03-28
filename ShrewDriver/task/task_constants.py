import sys
sys.path.append("..")

from util.enumeration import Enumeration

STATE_TIMEOUT = "TIMEOUT"
STATE_INIT = "INIT"
STATE_DELAY = "DELAY"
STATE_GRAY = "GRAY"
STATE_SPLUS = "SPLUS"
STATE_SMINUS = "SMINUS"
STATE_REWARD = "REWARD"

stateSet = [STATE_TIMEOUT, STATE_INIT, STATE_DELAY, STATE_GRAY, STATE_SPLUS, STATE_SMINUS, STATE_REWARD]
States = Enumeration("States", stateSet)

actionSet = ['LICK', 'LEAVE', 'TAP', 'LICK_DONE', 'TAP_DONE']
Actions = Enumeration("Actions", actionSet)

resultsSet = ['HIT', 'CORRECT_REJECT', 'TASK_FAIL', 'MISS', 'NO_RESPONSE', 'ABORT', 'FALSE_ALARM']
Results = Enumeration("Results", resultsSet)