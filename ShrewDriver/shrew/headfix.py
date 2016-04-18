from __future__ import division

import sys
sys.path.append("..")

from constants.task_constants import *

def load_parameters(task):
    print "Using settings for Headfix!"

    task.showInteractUI = True  # Enables the interact UI, used in headfixed training.

    task.screenDistanceMillis = 25
    task.rewardCooldown = 0.5 #If shrew has not licked for this many seconds, make reward available.
    task.rewardBolus = 100  # Microliters

