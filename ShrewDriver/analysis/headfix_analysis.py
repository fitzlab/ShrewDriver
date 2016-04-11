from __future__ import division
import sys
sys.path.append("..")


# Dummy class for now -- it may do some stuff later

from collections import deque
from trial.headfix_trial import *

class HeadfixAnalysis():

    def __init__(self, logFile=None, settingsFile=None, summaryFile=None):
        self.eventsToProcess = deque()
        
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
        return ""

    def process_line(self, line):
        print "Headfix >>>", line



