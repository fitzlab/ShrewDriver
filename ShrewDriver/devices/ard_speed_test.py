from __future__ import division
import sys
sys.path.append("..")


import time

import serial_port

def speed_test():
    ser = serial_port.SerialPort("COM100")
    time.sleep(2)
    ser.startReadThread()
    print "Reading..."

    ser.getUpdates()
    nSamples = 100
    sizes = [0] * nSamples
    for i in range(nSamples):
        time.sleep(1)
        updates = ser.getUpdates()
        print len(updates)
    

if __name__ == "__main__":
    speed_test()
