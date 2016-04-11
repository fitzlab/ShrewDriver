from __future__ import division
import sys
sys.path.append("..")


import random
import time

class State:

    def __init__(self, replay=False):
        self.name = ""
        self.screenCommand = ""
        self.actions = []

        #duration specifies how long in seconds it lasts; "None" means forever
        self.duration = None
        self.minDuration = None
        self.maxDuration = None

        #records when state started / ended
        self.startTime = 0
        self.endTime = 0

    def is_done(self):
        #are we done yet?

        if self.duration is None:
            #A "None" duration means time is not used as an end condition
            return False

        if self.replay:
            return (self.t - self.startTime) >= self.duration
        else:
            return (time.time() - self.startTime) >= self.duration

    def check_actions(self):
        for action in self.actions:
            action.attempt()

    def roll_duration(self):
        self.duration = random.random()*(self.maxDuration-self.minDuration) + self.minDuration

    def restart(self):
        #sets the start time to the current time, effectively restarting the state
        self.startTime = time.time()
