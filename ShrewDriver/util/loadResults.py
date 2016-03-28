
"""
Load trial data from a run
"""

import pickle
import sys
sys.path.append("..")

from task import task_nonmatch
from task.task_nonmatch import TrialNonMatch

def load_pickle_file(filePath):
    all_the_stuff = pickle.load(open(filePath))

    print all_the_stuff
    
    for thing in all_the_stuff:
        if isinstance(thing, list):
            #it's the trials
            for trial in thing:
                print "====="
                print trial.result
                
                print "\nStates:"
                for state in trial.stateHistory:
                    print str(state.name) + ": " + str(state.startTime) + " - " + str(state.endTime) + " [" + str(state.screenCommand) + "]"
                print ""
        elif isinstance(thing, tuple):
            #it's the lick and tap history
            (licks, taps) = thing
            print "\n\nLicks:"
            for lick in licks:
                print lick
            print "\n\nTaps:"
            for tap in taps:
                print tap
        else:
            #it's the params
            print "\n\nParams: \n" + str(thing.__dict__)
            
        

if __name__ == "__main__":
    load_pickle_file(r"C:\Users\fitzlab1\Documents\ShrewData\Queen\2015-12-17\0021\2015-12-17_0021_trials_and_params.pkl")