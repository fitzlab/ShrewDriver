"""
Talks to the Measurement Computing 1208-FS DAQ
Sends stimcodes to CED/Spike2.
"""

import time
import UniversalLibrary as UL

class MccDaq(object):
    
    def __init__(self):
        #DAQ setup        
        self.boardNum = 0
        UL.cbDConfigPort(self.boardNum, UL.FIRSTPORTA, UL.DIGITALOUT)
        UL.cbDConfigPort(self.boardNum, UL.FIRSTPORTB, UL.DIGITALOUT)
        
        #trigger bits for frame onset, stim onset, etc        
        self.triggerBits = [0,0,0,0,0,0,0,0]
        self.stimcodeReadBit = 0 #constant telling you which bit tells CED to read the current stimcode
        self.stimBit = 2 #constant telling you which bit is for stim on / off
        self.frameBit = 3 #constant telling you which bit is for frame flip triggers
        
    def send_stimcode(self, stimcode):
        """
        Puts a stimcode on the wires, then flips a bit to tell CED to read the code.
        """
        
        stimNumber = stimcode
        #send stimcode to CED via measurement computing DAQ
        UL.cbDOut(self.boardNum,UL.FIRSTPORTA,stimNumber)
        
        self.triggerBits[self.stimcodeReadBit] = 1
        UL.cbDOut(self.boardNum,UL.FIRSTPORTB,self.getTriggerValue())

        #Tell CED to read stimcode and set stim to "on"
        #this costs 1.2ms (+/- 0.1ms).
        self.triggerBits[self.stimcodeReadBit] = 0
        self.triggerBits[self.stimBit] = 1
        UL.cbDOut(self.boardNum,UL.FIRSTPORTB,self.getTriggerValue())
    
    def getTriggerValue(self):
        """
        Convert the trigger bits into a number value for output.
        """
        triggerValue = 0
        for i in range(len(self.triggerBits)):
            triggerValue += self.triggerBits[i] * pow(2,i)
        return triggerValue
        
if __name__ == "__main__":
    daq = MccDaq()
    
    for i in range(10):
        print "sending " + str(i) 
        daq.send_stimcode(i)
        time.sleep(1)