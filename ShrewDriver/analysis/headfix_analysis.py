from __future__ import division
import sys
sys.path.append("..")

import re
from collections import deque

class HeadfixAnalysis():

    def __init__(self, logFile=None, settingsFile=None, summaryFile=None):
        self.eventsToProcess = deque()

        self.totalmL = 0
        self.p = re.compile('\d+')
        
    def event(self, event):
        self.eventsToProcess.append(event)


    def process_events(self):
        """
        Process all the events in the deque. 
        Should be called at the end of each trial.
        Not threadsafe; expecting this to be used in-thread between trials.
        """
        while len(self.eventsToProcess) > 0:
            line = self.eventsToProcess.popleft()
            self.process_line(line)

    def get_results_str(self):
        return "Total mL: " + str(self.totalmL)

    def process_line(self, line):
        if "bolus" in line or "user_reward" in line:
            print line
            m = self.p.findall(line)
            mL = float(m[0] + "." + m[1])
            self.totalmL += mL



