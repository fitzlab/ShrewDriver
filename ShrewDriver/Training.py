from __future__ import division
import time, threading, random, sys

sys.path.append("./devices")
from SerialPort import *

sys.path.append("./util")
from Enumeration import *
import objectToString

sys.path.append("./global")
from Constants import *

sys.path.append("./sequencer")
from Sequencer import *

sys.path.append("./task")
from TaskGoNoGo import *

from LivePlot import *
from ShrewDriver import *
from Trial import *
from Analyzer import *

'''
Training.py is the control center. 
This is where the main loop lives (listen to sensors, send commands to screen, etc.)
It also controls live plotting and analysis.
'''


class Training():
    
    def __init__(self, shrewDriver):
        
        self.stopFlag = False
        self.shrewDriver = shrewDriver
        
        #start live plotting
        self.livePlot = LivePlot(self.shrewDriver.animalName)
        
        #start sensor serial
        self.arduinoSerial = SerialPort(self.shrewDriver.arduinoPortName)
        self.arduinoSerial.startReadThread()
        
        #start syringe pump serial
        self.syringeSerial = SerialPort(self.shrewDriver.syringePortName)
        self.syringeSerial.startReadThread()
        
        #start stim serial
        self.stimSerial = SerialPort(self.shrewDriver.stimPortName)
        self.stimSerial.startReadThread()
        
        #set up task
        self.task = TaskGoNoGo(self, shrewDriver)
        
        #start file logging
        self.logFilePath = self.shrewDriver.experimentPath + self.shrewDriver.sessionFileName + "_log.txt" 
        self.logFile = open(self.logFilePath, 'w')
        
        #make the live data analyzer
        self.analyzer = Analyzer(shrew=self.shrewDriver.animalName)
        
        #turn screen on, if needed
        time.sleep(0.1) 
        self.stimSerial.write('screenon\n')
    
    def mainLoop(self):
        while not self.stopFlag:
            #check serial
            updates = self.arduinoSerial.getUpdates()
            for update in updates:
                self.processUpdates(update)
            
            #update state
            self.task.checkStateProgression()
            
            #get results from other serial threads
            #Prevents potential serial buffer overflow bugs
            bunchaCrap = self.syringeSerial.getUpdates()
            bunchaCrap = self.stimSerial.getUpdates()
            #Don't do anything with that information because it's crap
    
    
    def processUpdates(self, inputStr):
        updateTokens = str.split(inputStr)
        evtType = updateTokens[0]
        timestamp = float(updateTokens[1])
        self.task.sensorUpdate(evtType, timestamp)
        
        self.logPlotAndAnalyze(evtType, timestamp)
        
    
    def logPlotAndAnalyze(self, eventType, timestamp):
        self.livePlot.sigEvent.emit(eventType, timestamp)
        line = eventType + " " + str(timestamp) + "\n"
        self.logFile.write(line)
        self.analyzer.processLine(line)
        
    
    def dispenseHint(self, rewardMillis):
        timestamp = time.time()
        self.logPlotAndAnalyze("RL", timestamp)
        self.logPlotAndAnalyze("hint:" + str(rewardMillis), + timestamp)
        self.syringeSerial.write(str(int(rewardMillis*1000)) + "\n")
    
    def dispenseReward(self, rewardMillis):
        timestamp = time.time()
        self.logPlotAndAnalyze("RH", timestamp)
        self.logPlotAndAnalyze("bolus:" + str(rewardMillis), timestamp)
        self.syringeSerial.write(str(int(rewardMillis*1000)) + "\n")
    
    def blackScreen(self):
        #used by "stop recording" to black out screen at end of experiment
        self.stimSerial.write('as pab px0 py0 sx999 sy999\n')
        time.sleep(0.05)
        self.stimSerial.write('screenoff\n')
    
    def stop(self):
        #end logfile
        self.logFile.close()
        
        #stop training thread and reset screen
        self.stopFlag = True
        time.sleep(0.01)
        self.blackScreen()
        time.sleep(0.5)
        
        #stop serial thread
        self.syringeSerial.close()
        self.arduinoSerial.close()
        self.stimSerial.close()
        
    
    def start(self):
        self.stopFlag = False
        
        self.task.start()
        
        #threading /  main loop stuff goes here
        thread = threading.Thread(target=self.mainLoop)
        thread.daemon = True
        thread.start()

if __name__ == '__main__':
    print "run ShrewDriver.py instead!"
