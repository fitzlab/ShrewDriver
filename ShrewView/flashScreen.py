from __future__ import division
from SerialPort import SerialPort
import time, pygame, random

serSend = SerialPort('COM9')
serSend.startReadThread()

nTrials = 1000
i = 0
state = 0
delayMillis = 20000
changedAt = time.time()
while i < nTrials:
    waitTime = int(delayMillis-(time.time() - changedAt)*1000)
    print str(waitTime)
    pygame.time.delay(waitTime)
    if state == 1:
        print str(waitTime)
        changedAt = time.time()
        serSend.write("b\n")
        state = 0
    elif state == 0:
        changedAt = time.time()
        serSend.write("g\n")
        state = 1
    
 