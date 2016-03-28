
# Dummy class for now -- it may do some stuff later

from collections import deque, namedtuple


class HeadfixOnlineAnalyzer():
    
   
    def __init__(self, settingsFile, summaryFile):
        self.eventsToProcess = deque()
        self.analyzer = HeadfixAnalyzer()
        
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
            self.analyzer.process_line(line) 
        
        summary = self.analyzer.get_summary()
        
        return summary   
    
class HeadfixAnalyzer():

    def __init__(self):
        pass
        
    def get_summary(self):
        return ""
    
    def process_line(self, line):
        print ">>>",line
    