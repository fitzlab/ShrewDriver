from __future__ import division

"""
Butters's stim was used in anesthetized and awake imaging.
"""

import time
import datetime
from collections import deque
import pickle
import os
import sys

sys.path.append("..")

def make_trial_script(
    t_timeout=2, 
    t_init = 1, 
    t_grating = 0.5, 
    t_timingDelay = 0.5, 
    t_responsePeriod = 1.0, 
    t_memoryDelay = 1.0,
    jitter = " jf3 ja0.25 ",
    splus = " sqr135 ",
    sminus = " sqr160 ",
    rfPos = " px0 py0 ",
    nTrials=12
):

    """
    Build an array of stim events, make a StimScript out of it, and return.
    """    
    events = []  
    t=0  
    for i in xrange(nTrials):
        #=== 3-grating trial ===#
        events.append( StimEvent(startTime=t, command="ac pab sx12 sy12"+rfPos, stimcode=0) ) #Timeout
        t+=t_timeout
        events.append( StimEvent(startTime=t, command="ac paw sx12 sy12"+rfPos, stimcode=1) ) #Init
        t+=t_init
        events.append( StimEvent(startTime=t, command="sx0 sy0", stimcode=2) ) #TimingDelay
        t+=t_timingDelay
        events.append( StimEvent(startTime=t, command="as sf0.25 tf0 px0 py0 sx999 sy999"+sminus+jitter, stimcode=3) ) #Sample Grating
        t+=t_grating
        events.append( StimEvent(startTime=t, command="sx0 sy0", stimcode=4) ) #Memory Delay
        t+=t_memoryDelay
        events.append( StimEvent(startTime=t, command="as sf0.25 tf0 px0 py0 sx999 sy999"+sminus+jitter, stimcode=5) ) #Match
        t+=t_grating
        events.append( StimEvent(startTime=t, command="sx0 sy0", stimcode=6) ) #Response Period (false alarm)
        t+=t_responsePeriod
        events.append( StimEvent(startTime=t, command="as sf0.25 tf0 px0 py0 sx999 sy999"+splus+jitter, stimcode=7) ) #Nonmatch
        t+=t_grating
        events.append( StimEvent(startTime=t, command="sx0 sy0", stimcode=8) ) #Nonmatch Response Period (correct reject)
        t+=t_responsePeriod

        #=== 2-grating trial ===#
        events.append( StimEvent(startTime=t, command="ac pab sx12 sy12"+rfPos, stimcode=0) ) #Timeout
        t+=t_timeout
        events.append( StimEvent(startTime=t, command="ac paw sx12 sy12"+rfPos, stimcode=1) ) #Init
        t+=t_init
        events.append( StimEvent(startTime=t, command="sx0 sy0", stimcode=2) ) #TimingDelay
        t+=t_timingDelay
        events.append( StimEvent(startTime=t, command="as sf0.25 tf0 px0 py0 sx999 sy999"+sminus+jitter, stimcode=3) ) #Sample Grating
        t+=t_grating
        events.append( StimEvent(startTime=t, command="sx0 sy0", stimcode=4) ) #Memory Delay
        t+=t_memoryDelay
        events.append( StimEvent(startTime=t, command="as sf0.25 tf0 px0 py0 sx999 sy999"+splus+jitter, stimcode=7) ) #Nonmatch
        t+=t_grating
        events.append( StimEvent(startTime=t, command="sx0 sy0", stimcode=8) ) #Nonmatch Response Period (hit)
        t+=t_responsePeriod
    
    script = StimScript(events)  
    return script



if __name__ == "__main__":
    """
    Runs a stim script that's based on Chico / Queen's task. 
    Default params are exactly what we're doing in training right now.
    Parameters can be easily changed if needed; see make_trial_script declaration below.
    
    Spike2 will receive stimcodes, so make sure to start that first.
    """
    script = make_trial_script(
        t_grating=0.5, 
        t_memoryDelay=1.0, 
        t_responsePeriod=1.0, 
        splus = " sqr65 ",
        sminus = " sqr90 ",
        nTrials=12)
    
    #=== Setup ===#
    script.stimDevice.write("screendist25")
    time.sleep(0.2)
    script.save()
    script.run()
    
    