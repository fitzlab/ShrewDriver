from __future__ import division
import sys
sys.path.append("..")


import time
import threading
import random

from devices.serial_port import SerialPort
from devices.psycho import *
from devices.air_puff import AirPuff

from util.enumeration import *
from util.serialize import *
from constants.task_constants import *

from sequencer.sequencer_base import *

from task.task_discrimination import *
from task.task_headfix import *


from ui.live_plot import *
from shrewdriver import *
from task.trial import *

from analysis.discrimination_analysis import *
from analysis.headfix_analysis import *

'''
Training.py is the control center. 
This is where the main loop lives (listen to sensors, send commands to screen, etc.)
It also controls live plotting, analysis, and camera recording.
'''

class Training():
    
    def __init__(self, shrewDriver):
        
        self.stopFlag = False
        self.shrewDriver = shrewDriver

        #start live plotting
        self.livePlot = LivePlot(self.shrewDriver.animalName)

        #start camera
        self.cameraReader = None
        self.startCamera()

        #start sensor serial
        print("sensors " + str(self.shrewDriver.sensorPortName))
        self.sensorSerial = SerialPort(self.shrewDriver.sensorPortName)
        self.sensorSerial.startReadThread()
        
        #start syringe pump serial
        self.syringeSerial = SerialPort(self.shrewDriver.syringePortName)
        self.syringeSerial.startReadThread()

        #start air puff serial, if any
        self.airPuff = None
        if self.shrewDriver.airPuffPortName != None:
            self.airPuff = AirPuff(self.shrewDriver.airPuffPortName)

        #start stim serial
        if self.shrewDriver.stimPortName == "PsychoPy":
            #If we're upstairs, use PsychoPy to render stims
            time.sleep(5)  #lets users drag windows around.
            self.stimSerial = Psycho(windowed=False)
        else:
            self.stimSerial = SerialPort(self.shrewDriver.stimPortName)
            self.stimSerial.startReadThread()
        
        #set up task
        if self.shrewDriver.animalName == 'Headfix':
            self.task = TaskHeadfix(self, shrewDriver)
        else:
            self.task = TaskDiscrimination(self, shrewDriver)

        #make interact window, if needed
        if hasattr(self.task, "showInteractUI") and self.task.showInteractUI:
            self.shrewDriver.show_interact_ui(self.task)

        #start file logging
        self.logFilePath = self.shrewDriver.experimentPath + self.shrewDriver.sessionFileName + "_log.txt" 
        self.logFile = open(self.logFilePath, 'w')
        
        #make the live data analyzer
        if self.shrewDriver.animalName == "Headfix":
            self.analyzer = HeadfixAnalysis(logFile=None, settingsFile=self.task.settingsFilePath)
        else:
            self.analyzer = DiscriminationAnalysis(logFile=None, settingsFile=self.task.settingsFilePath)
        
        #turn screen on, if needed
        time.sleep(0.1) 
        self.stimSerial.write('screenon\n')
    
    def mainLoop(self):
        while not self.stopFlag:
            #check serial
            updates = self.sensorSerial.getUpdates()
            for update in updates:
                self.processUpdates(update)

            #update state
            self.task.checkStateProgression()

            t0 = time.time()
            self.livePlot.update()
            t1 = time.time

            #get results from other serial threads
            #Prevents potential serial buffer overflow bugs
            bunchaCrap = self.syringeSerial.getUpdates()
            bunchaCrap = self.stimSerial.getUpdates()
            #Don't do anything with that information because it's crap
    
    
    def processUpdates(self, update):
        evtType = update[0]
        timestamp = float(update[1])
        self.task.sensorUpdate(evtType, timestamp)

        self.logPlotAndAnalyze(evtType, timestamp)

    
    def logPlotAndAnalyze(self, eventType, timestamp):
        self.livePlot.sigEvent.emit(eventType, timestamp)
        line = eventType + " " + str(timestamp) + "\n"
        self.logFile.write(line)
        self.analyzer.process_line(line)
        
    
    def dispenseHint(self, rewardMillis):
        timestamp = time.time()
        self.logPlotAndAnalyze("RL", timestamp)
        self.logPlotAndAnalyze("hint:" + str(rewardMillis), + timestamp)
        self.syringeSerial.write(str(int(rewardMillis*1000)) + "\n")
        print "I just sent " + str(int(rewardMillis*1000))
    
    def dispenseReward(self, rewardMillis):
        timestamp = time.time()
        self.logPlotAndAnalyze("RH", timestamp)
        self.logPlotAndAnalyze("bolus:" + str(rewardMillis), timestamp)
        self.syringeSerial.write(str(int(rewardMillis*1000)) + "\n")
        print "r just sent " + str(int(rewardMillis*1000))

    def send_stimcode(self, stimCode):
        pass
        #print "Not sending stimcode " + str(stimCode) + " because this isn't implemented yet."

    def blackScreen(self):
        #used by "stop recording" to black out screen at end of experiment
        self.stimSerial.write('as pab px0 py0 sx999 sy999\n')
        time.sleep(0.05)
        self.stimSerial.write('screenoff\n')
    
    def stop(self):
        #end logfile
        self.logFile.close()

        #close camera
        self.stopCamera()

        #stop training thread and reset screen
        self.stopFlag = True
        time.sleep(0.01)
        self.blackScreen()
        time.sleep(0.5)
        
        #stop serial thread
        self.syringeSerial.close()
        self.sensorSerial.close()
        self.stimSerial.close()
        
    
    def start(self):
        self.stopFlag = False
        self.task.start()
        
        #threading /  main loop stuff goes here
        thread = threading.Thread(target=self.mainLoop)
        thread.daemon = True
        thread.start()

    def startCamera(self):
        """begin live view and recording from camera"""

        #get UI information from shrewdriver
        self.experimentPath = self.shrewDriver.experimentPath
        self.sessionFileName = self.shrewDriver.sessionFileName
        self.cameraID = self.shrewDriver.cameraID
        self.animalName = self.shrewDriver.animalName

        try:
            vidPath = self.experimentPath + self.sessionFileName + '.avi'
            print 'Recording video to ' + vidPath
            self.cameraReader = CameraReader(self.cameraID, vidPath, self.animalName)
            self.cameraReader.startReadThread()
        except:
            print "Couldn't start camera."
            traceback.print_exc()

    def stopCamera(self):
        if self.cameraReader is not None:
            self.cameraReader.stopFlag = True


if __name__ == '__main__':
    print "run ShrewDriver.py instead!"
