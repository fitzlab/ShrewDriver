from __future__ import division
import time, pygame, random, sys

from SerialPort import SerialPort

serSend = SerialPort('COM9')
serSend.startReadThread()

nTrials = 1000
i = 0
state = 0
delayMillis = 500
changedAt = time.time()
while i < nTrials:
    waitTime = int(delayMillis-(time.time() - changedAt)*1000)
    pygame.time.delay(waitTime)
    if state == 1:
        print str(waitTime)
        serSend.write("b\n")
        serSend.write("b\n")
        changedAt = time.time()
        state = 0
    elif state == 0:
        serSend.write("g\n")
        serSend.write("g\n")
        changedAt = time.time()
        state = 1
    
 