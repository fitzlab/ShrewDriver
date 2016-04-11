import time
import functools
import random
import sys

from collections import OrderedDict

sys.path.append('..')
from util.cond_event import CondEvent

from devices.arduino_sensor import ArduinoSensor
from devices.syringe_pump import SyringePump
from devices.stimbot import Stimbot
from devices.psycho import Psycho

from task import *

'''
Headfix Task

A simple task where the shrew can lick and receive juice rewards.
Named because it is especially useful in acclimation to head-fixation,
but useful in other acclimations as well.

- Only uses the lick sensor
- Screen is optional (will display black if on.)
'''

class ParamsHeadfix(Params):
    
    def __init__(self):
        # Note that these parameters are defaults only!
        # They will be overridden by anything in the shrew-specific file.
        
        self.reward_mL = 0.2

class TrialHeadfix(Trial):
    def __init__(self):
        super(TrialHeadfix, self).__init__()
        pass
        

class TaskHeadfix(Task):
    
    def __init__(self, shrew):
        super(TaskHeadfix, self).__init__(shrew)
        self.params = None
        self._initMode = None

        self.trial = None
        self.trialHistory = []

    def run(self):
        self.stateHistory = []
        self.trial = TrialHeadfix()
        self.changeState(self.states["Timeout"])

        self.finished = False #change to True to stop running
        
        while not self.finished:
            updates = self.ardSensor.checkSensors()
            self.currentState.checkActions()
            
            if self.tracer is not None:
                #update tracer with new sensor information
                self.update_tracer(updates)            

            time.sleep(self.PULSE_TIME) #allow other threads to run, e.g. psychopy
        
    def setUpStates(self):
        #declare all states
        self.states = OrderedDict()
        self.states["Timeout"] = State()
        self.states["Init"] = State()
        self.states["Reward"] = State()
        
        #make functions for changing to each state        
        self.changeTo = {}
        for key in self.states.keys():
            self.changeTo[key] = functools.partial(self.changeState, self.states[key])
            self.states[key].name = key  #tell each state what its name is
            
        #Timeout
        self.states["Timeout"].duration = 3
        self.states["Timeout"].screenCommand = "as pag sx999 sy999\n"
        self.states["Timeout"].actions.append( CondEvent([self.states["Timeout"].isDone], self.changeTo["Init"], "done") )
        self.states["Timeout"].actions.append( CondEvent([self.ardSensor.isLicking], self.states["Timeout"].restart, "lickRestart") )
        
        #Init
        self.states["Init"].duration = None
        self.states["Init"].screenCommand = "as pag sx999 sy999\n"
        self.states["Init"].actions.append( CondEvent([], self.changeTo["Reward"], Task.INIT_AUTO) )
        
        #Reward
        self.states["Reward"].screenCommand = "as pag sx999 sy999\n"
        self.states["Reward"].actions.append( CondEvent([self.ardSensor.isLicking], [self.reward, self.changeTo["Timeout"]], "lickReward") )
        
    
    def changeState(self, newState):
        self.currentState = newState
        self.currentState.startTime = time.time()
        
        print "State changed to " + newState.name
        
        screenCommand = self.currentState.screenCommand

        #add any state specific conditionals, e.g. grating orientations, phases, or duration, then write to stimbot
        self.stimDevice.write(screenCommand)
        
        #begin new state
        self.stateStart = time.time()
    
    #trial outcomes
    def reward(self):
        self.dispense(self.params.reward_mL)

    @property
    def initMode(self):
        return self._initMode

    @initMode.setter
    def initMode(self, value):
        self._initMode = value
        print "setting initmode"

        #first, remove any actions associated with init modes
        for key in self.states.keys():
            state = self.states[key]
            for action in state.actions:
                if action.name in Task.initModes:
                    state.actions.remove(action)
        
        #now add actions to states according to the given init mode
        if self._initMode == Task.INIT_AUTO:
            self.states["Init"].actions.append( CondEvent([], self.changeTo["Reward"], Task.INIT_AUTO) )
        elif self._initMode == Task.INIT_IR:
            self.states["Init"].actions.append( CondEvent(self.ardSensor.isInIR, self.changeTo["Reward"], Task.INIT_IR) )
        elif self._initMode == Task.INIT_LICK:
            self.states["Init"].actions.append( CondEvent(self.ardSensor.isLicking, self.changeTo["Reward"], Task.INIT_LICK) )
        elif self._initMode == Task.INIT_TAP:
            self.states["Init"].actions.append( CondEvent(self.ardSensor.isTapping, self.changeTo["Reward"], Task.INIT_TAP) )
        

    def startTrial(self):
        """Triggered by UI. Changes state from Timeout or Init to the first state in the trial."""
        if self.currentState == self.states["Timeout"] or self.currentState == self.states["Init"]:
            self.changeTo["Reward"]()

    def taskFail(self):
        print "Task failed"
        self.changeState(self.states["Timeout"])


if __name__ == "__main__":
    print "Headfix task starting..."

    task = TaskHeadfix()
    task.ardSensor = ArduinoSensor("COM90")
    task.syringePump = SyringePump("COM91")
    task.stimDevice = Psycho()
    
    task.params = ParamsHeadfix()
    
    task.setUpStates()
    task.initMode = Task.INIT_TAP
    
    task.run()
    
