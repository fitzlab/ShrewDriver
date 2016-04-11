import time
import datetime
import threading
import os
import re
import itertools
import random
import pickle
import sys
import copy

sys.path.append("..")
from ui import launch
from ui import tracer
from ui import interact

from output.logging import Log

from devices.psycho import Psycho
from devices.syringe_pump import SyringePump
from devices.arduino_sensor import ArduinoSensor
from devices.camera_reader import CameraReader


class Params(object):

    PHASE_DISCRIMINATION = "phase discrimination" #not implemented; maybe someday
    ORIENTATION_DISCRIMINATION = "orientation discrimination"

    def __init__(self):
        self.discriminationType = self.ORIENTATION_DISCRIMINATION

    #common functions
    def getNonMatchingPair(self, list1, list2):
        """
        Given two lists, picks an element from each list such that the elements do not match. 
        Returns a tuple containing the two elements.

        Example:
        Returns a tuple (sPlus, sMinus) where sPlus != sMinus, chosen from sMinusOrientations and sPlusOrientations.
        Used in task_discrim and task_nonmatch.
        """
        all_pairs = list(itertools.product(list1, list2))
        distinct_pairs = []
        for pair in all_pairs:
            #elements are considered equal if within 0.0001 degrees. Prevents float errors.
            if abs(pair[0] - pair[1]) > 0.0001:
                distinct_pairs.append(pair)

        return random.choice(distinct_pairs)        

class Trial(object):

    def __init__(self):
        self.stateHistory = []


class Task(object):

    #constants
    PULSE_TIME = 0.010 #seconds between each sensor check

    INIT_TAP = "init_tap"
    INIT_LICK = "init_lick"
    INIT_AUTO = "init_auto"
    INIT_IR = "init_ir"
    initModes = [INIT_TAP, INIT_LICK, INIT_AUTO, INIT_IR]
    

    def __init__(self, shrew):
        self.shrew = shrew

        self.startTime = time.time()

        #device setup
        self.ardSensor = ArduinoSensor(self.shrew.ardSensorPort)
        self.syringePump = SyringePump(self.shrew.syringePort)  

        if self.shrew.stimDevice is not None:
            self.stimDevice = self.shrew.stimDevice
        else:
            self.stimDevice = Stimbot(self.shrew.stimbotPort)
            
        self.stimDevice.write('screendist' + str(self.shrew.screenDist) + "\n")

    #--- Common functions used by all task types ---#
    def makeTrialSequencer(self):
        
        pass        

    def dispense(self, mL):
        self.syringePump.bolus(mL)
        #record mL used
        self.mainLog.write("reward " + str(mL))
        print "dispensed " + str(mL) + "mL, total " + str(self.syringePump.total_mL) + " mL"


    def update_tracer(self, updates):
        for update in updates:
            (data, t) = update
            toks = data.rstrip().split()
            if len(toks) < 2 or not toks[1].isdigit:
                continue
            try:
                level = int(toks[1])
                elapsed = float(t) - self.startTime
                if toks[0] == "L":
                    self.tracer.sig_add_data.emit("Lick", elapsed, level)
                if toks[0] == "T":
                    self.tracer.sig_add_data.emit("Tap", elapsed, level)
            except:
                continue            

    def save_data(self):
        """ 
        Called at the end of each trial.
        Flushes log output.
        Saves params and trials to pickle files.
        """
        
        if hasattr(self, "mainLog") and self.mainLog is not None:    
            self.mainLog.flush()    
        
        if hasattr(self, "outFilePathPkl"):
            pickle.dump((self.trialHistory, self.params, (self.ardSensor.historyLick, self.ardSensor.historyTap)), open(self.outFilePathPkl, 'wb'))
    
    def _ui_setup(self, qtThread):
        #called once PyQt is running. 
        self.uiThread = qtThread
        
        #add "lick" and "tap" plots to the UI
        self.tracer.sig_add_trace.emit("Lick")  
        self.tracer.sig_add_trace.emit("Tap")     
    
        #Define thresholds on the tracer
        self.tracer.sig_set_threshold.emit("Lick", self.ardSensor.lickThreshold)  
        self.tracer.sig_set_threshold.emit("Tap", self.ardSensor.tapThreshold)        
        
        self.run()   

    def initialize_daq(self):
        try:
            print "Initializing DAQ..."
            #The import takes several seconds so it's best to do it
            #in the midst of the code, rather than at the top of the file.
            from devices.daq import MccDaq
            sys.stdout.flush()
            self.daq = MccDaq()
        except:
            print "Warning: No Measurement Computing DAQ available."
            
            
    #--- UI callbacks ---#
    def ui_fail_task(self):
        print "Failing task at user's request"
        self.mainLog.write("User signaled a task fail")
        self.taskFail()
        
    def ui_start_trial(self):
        print "Starting trial at user's request"
        self.mainLog.write("User started trial")
        self.startTrial()
        
    def ui_dispense(self, mL):
        print "Giving " + str(mL) + " mL"
        self.mainLog.write("User gave shrew juice")
        self.dispense(mL)


#--- Main function, for testing only. Please use shrew files to start specific tasks. ---#
if __name__ == "__main__":
    #test out the State class for replayability
    print "Running tests on State class"

    s = State(replay=False)
    s.duration = 2
    s.restart()
    while not s.isDone():
        pass
    assert (time.time() - s.startTime) >= 2
    
    s2 = State(replay=True)
    s2.duration = 2
    s2.restart()
    s2.t = time.time() + 2
    assert s2.isDone() == True

    print "Tests complete!"