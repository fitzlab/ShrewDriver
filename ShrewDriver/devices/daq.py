from __future__ import division
import sys
sys.path.append("..")


import traceback

"""
Talks to the Measurement Computing 1208-FS DAQ
Sends stimcodes to CED/Spike2.
"""

import time
from constants.task_constants import *

class MccDaq(object):
    
    def __init__(self):
        """
        Returns a Measurement Computing daq object, if possible.
        Returns None if
        """
        self.UL = None
        print "MCC DAQ: Connecting..."
        try:
            import UniversalLibrary as UL
            self.UL = UL
        except:
            print "Could not open Measurement Computing DAQ. "
            print "Check that the daq is connected. Also, ensure InstaCal and PyUniversalLibrary are installed."
            print "DAQ output will be unavailable for this session."
            traceback.print_exc()
            return
        print "MCC Daq: Success!"

        # DAQ setup
        self.boardNum = 0
        UL.cbDConfigPort(self.boardNum, UL.FIRSTPORTA, UL.DIGITALOUT)
        UL.cbDConfigPort(self.boardNum, UL.FIRSTPORTB, UL.DIGITALOUT)
        
        # trigger bits for frame onset, stim onset, etc
        self.triggerBits = [0,0,0,0,0,0,0,0]
        self.stimcodeReadBit = 0 # constant telling you which bit tells CED to read the current stimcode
        self.stimBit = 2  # constant telling you which bit is for stim on / off
        self.frameBit = 3  # constant telling you which bit is for frame flip triggers
        
    def send_stimcode(self, stimcode):
        """
        Puts a stimcode on the wires, then flips a bit to tell CED to read the code.
        Stimcode values from 0 to 127 should be fine.
        """

        if self.UL is None:
            #if we didn't open the DAQ, don't do anything here.
            return

        stimNumber = stimcode
        #send stimcode to CED via measurement computing DAQ
        self.UL.cbDOut(self.boardNum, self.UL.FIRSTPORTA, stimNumber)
        
        self.triggerBits[self.stimcodeReadBit] = 1
        self.UL.cbDOut(self.boardNum, self.UL.FIRSTPORTB, self.getTriggerValue())

        #Tell CED to read stimcode and set stim to "on"
        #this costs 1.2ms (+/- 0.1ms).,m
        self.triggerBits[self.stimcodeReadBit] = 0
        self.triggerBits[self.stimBit] = 1
        self.UL.cbDOut(self.boardNum, self.UL.FIRSTPORTB, self.getTriggerValue())

    def getTriggerValue(self):
        """
        Convert the trigger bits into a number value for output.
        """
        triggerValue = 0
        for i in range(len(self.triggerBits)):
            triggerValue += self.triggerBits[i] * pow(2, i)
        return triggerValue
        
if __name__ == "__main__":
    daq = MccDaq()
    
    for i in range(10):
        print "sending " + str(i) 
        daq.send_stimcode(i)
        time.sleep(1)