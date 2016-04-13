import time
import functools
import random
import sys
import itertools
from collections import OrderedDict

sys.path.append('..')
from util.cause_effect import CauseEffect

from task import *

class ParamsDiscrim(Params):

    def __init__(self):
        # Note that these parameters are defaults only!
        # They will be overridden by anything in the shrew-specific file.
        
        self.reward_mL = 0.2
        self.reward_hard_mL = 0.3
        
        self.sMinusOrientations = [0]
        self.sPlusOrientations = [45]
        
        self.timingDelayMin = 0.5
        self.timingDelayMax = 1.25
        
        self.hintChance = 0.0
        self.hintBolus = 0.03
        
        self.hitBolus = 0.150
        self.correctRejectBolus = 0.250
        
        self.noGoChance = 0.5
        
class TrialDiscrim(Trial):
    """
    A new trial object is made for each trial, so randomization can happen here.
    """
    
    GO = "go"
    NOGO = "nogo"

    def __init__(self, params):
        super(TrialDiscrim, self).__init__()

        self.params = params

        #roll trial type
        self.trialType = self.GO
        if random.random() > self.params.noGoChance:
            self.trialType = self.NOGO
            
        #roll hints
        self.hint = False
        if random.random() < self.params.hintChance:
            self.hint = True
    
        #oris
        oris = self.params.getNonMatchingPair(self.params.sMinusOrientations, self.params.sPlusOrientations)
        self.sMinusOri = oris[0]
        self.sPlusOri = oris[1]
        
        #phases
        self.phaseSPlus = round(random.random(), 2)
        self.phaseSMinus = round(random.random(), 2)
        self.phaseSPlusFinal = round(random.random(), 2)
        
        #roll timing delay
        self.timingDelay = random.uniform(self.params.timingDelayMin, self.params.timingDelayMax)     
    

class TaskDiscrim(Task):
    
    def __init__(self, shrew):
        super(TaskDiscrim, self).__init__(shrew)
        self.params = None

        self._initMode = None

        self.trial = None
        self.trialHistory = []
        
    def run(self):
        self.finished = False #change to True to stop running

        self.changeState(self.states["Timeout"])    
        
        while not self.finished:
            updates = self.ardSensor.checkSensors()
            self.currentState.checkActions()

            if self.tracer is not None:
                #update tracer with new sensor information
                self.update_tracer(updates)
                
            time.sleep(self.PULSE_TIME) #allow other threads to run
     
   
    def setUpStates(self):
        #declare all states
        self.states = OrderedDict()
        self.states["Timeout"] = State()
        self.states["Init"] = State()
        self.states["TimingDelay"] = State()
        self.states["SPlus"] = State()
        self.states["SPlusResponse"] = State()
        self.states["SMinus"] = State()
        self.states["SMinusResponse"] = State()
        self.states["SPlusFinal"] = State()
        self.states["SPlusFinalResponse"] = State()
        
        #make functions for changing to each state        
        self.changeTo = {}
        for key in self.states.keys():
            self.changeTo[key] = functools.partial(self.changeState, self.states[key])
            self.states[key].name = key  #tell each state what its name is
            
        #Timeout
        self.states["Timeout"].duration = 1
        self.states["Timeout"].actions.append( CauseEffect([self.states["Timeout"].isDone], self.changeTo["Init"], "stopTapping") )    

        #Init
        self.states["Init"].duration = None
        self.states["Init"].actions.append( CauseEffect([self.states["Init"].isDone], self.changeTo["TimingDelay"], "done") )
        
        #TimingDelay
        self.states["TimingDelay"].duration = None
        self.states["TimingDelay"].actions.append( CauseEffect([self.states["TimingDelay"].isDone, self.isGoTrial], self.changeTo["SPlus"], "done") )
        self.states["TimingDelay"].actions.append( CauseEffect([self.states["TimingDelay"].isDone, self.isNoGoTrial], self.changeTo["SMinus"], "done") )
        
        #SPlus
        self.states["SPlus"].duration = 0.5
        self.states["SPlus"].actions.append( CauseEffect([self.states["SPlus"].isDone], self.changeTo["SPlusResponse"], "done") )

        #SPlusResponse      
        self.states["SPlusResponse"].duration = 1
        self.states["SPlusResponse"].actions.append( CauseEffect([self.ardSensor.isLicking], self.hit, "hit") )
        self.states["SPlusResponse"].actions.append( CauseEffect([self.states["SPlusResponse"].isDone], self.miss, "miss") )
        
        #SMinus
        self.states["SMinus"].duration = 0.5
        self.states["SMinus"].actions.append( CauseEffect([self.states["SMinus"].isDone], [self.changeTo["SMinusResponse"], self.doHint], "done") )
        
        #SMinusResponse
        self.states["SMinusResponse"].duration = 1
        self.states["SMinusResponse"].actions.append( CauseEffect([self.ardSensor.isLicking], self.falseAlarm, "falseAlarm") )
        self.states["SMinusResponse"].actions.append( CauseEffect([self.states["SMinusResponse"].isDone], [self.changeTo["SPlusFinal"], self.doHint], "done") )

        #SPlusFinal
        self.states["SPlusFinal"].duration = 0.5
        self.states["SPlusFinal"].actions.append( CauseEffect([self.states["SPlusFinal"].isDone], [self.changeTo["SPlusFinalResponse"], self.doHint], "done") )
        
        #SPlusFinalResponse
        self.states["SPlusFinalResponse"].duration = 1
        self.states["SPlusFinalResponse"].actions.append( CauseEffect([self.ardSensor.isLicking], self.correctReject, "correctReject") )
        self.states["SPlusFinalResponse"].actions.append( CauseEffect([self.states["SPlusFinalResponse"].isDone], self.taskFail, "noResponseFail") )
        
        #Add task fails to most states for licking
        for key in self.states.keys():
            if key in ("TimingDelay", "SPlus", "SMinus", "SPlusFinal"):
                self.states[key].actions.append( CauseEffect([self.ardSensor.isLicking], self.taskFail, "lickFail") )    

    def newTrial(self):
        if self.trial is not None:
            self.trialHistory.append(self.trial)
            self.mainLog.write("Trial result: " + self.trial.result)
        self.trial = TrialDiscrim(self.params)        
        self.states["TimingDelay"].duration = self.trial.timingDelay

    def changeState(self, newState):
        if newState.name == "Timeout":
            self.newTrial()

        self.mainLog.write("State changed to " + newState.name)
        print "State changed to " + newState.name

        self.currentState = newState
        self.currentState.startTime = time.time()
        
        #begin new state
        self.stateStart = time.time()
        
        #build screen command, including grating orientation and phase if needed
        oriCmd = ""
        phaseCmd = ""
        if newState.name == "SPlus":
            oriCmd = "sqr" + str(self.trial.sPlus) + " "
            phaseCmd = "ph" + str(self.trial.phaseSPlus) + " "
        elif newState.name == "SMinus":
            oriCmd = "sqr" + str(self.trial.sMinus) + " "
            phaseCmd = "ph" + str(self.trial.phaseSMinus) + " "
        elif newState.name == "SPlusFinal":
            oriCmd = "sqr" + str(self.trial.sPlus) + " "
            phaseCmd = "ph" + str(self.trial.phaseSPlusFinal)

        self.stimDevice.write(oriCmd + phaseCmd + self.currentState.screenCommand)
        
    @property
    def initMode(self):
        return self._initMode

    @initMode.setter
    def initMode(self, value):
        self._initMode = value
        print "setting initmode to ", value 

        #first, remove any actions associated with init modes
        for key in self.states.keys():
            state = self.states[key]
            for action in state.actions:
                if action.name in Task.initModes:
                    state.actions.remove(action)
        
        #initAuto
        if self._initMode == Task.INIT_AUTO:
            pass

        #initIR
        if self._initMode == Task.INIT_IR:
            for key in self.states.keys():
                if key != "Timeout":
                    self.states[key].actions.append( CauseEffect([self.ardSensor.isNotInIR], self.taskFail, Task.INIT_IR) )        
            
        #initTap
        if self._initMode == Task.INIT_TAP:
            for key in self.states.keys():
                if key == "Init":
                    self.states[key].actions.append( CauseEffect([self.ardSensor.isTapping], self.changeTo["TimingDelay"], Task.INIT_TAP) )        
            

    def doHint(self):
        if self.trial.hint:
            self.dispense(self.params.hintBolus)

    #trial outcomes
    def hit(self):
        print self.RESULT_HIT
        self.trial.result = self.RESULT_HIT
        self.dispense(self.params.hitBolus)
        self.changeTo["Timeout"]()
        
    def miss(self):
        print self.RESULT_MISS
        self.trial.result = self.RESULT_MISS
        self.changeTo["Timeout"]()

    def correctReject(self):
        print self.RESULT_CORRECT_REJECT
        self.trial.result = self.RESULT_CORRECT_REJECT
        self.dispense(self.params.correctRejectBolus)
        self.changeTo["Timeout"]()

    def falseAlarm(self):
        print self.RESULT_FALSE_ALARM
        self.trial.result = self.RESULT_FALSE_ALARM
        self.changeTo["Timeout"]()        
    
    def taskFail(self):
        print self.RESULT_TASK_FAIL
        self.trial.result = self.RESULT_TASK_FAIL
        self.changeTo["Timeout"]()

    def isMatchTrial(self):
        return self.trial.trialType == TrialNonMatch.MATCH

    def isNonMatchTrial(self):
        return self.trial.trialType == TrialNonMatch.NONMATCH    
    
    RESULT_HIT = "hit"
    RESULT_MISS = "miss" 
    RESULT_CORRECT_REJECT = "correct reject"
    RESULT_FALSE_ALARM = "false alarm" 
    RESULT_TASK_FAIL = "task fail"   


if __name__ == "__main__":
    print "I am starting..."
    task = TaskNonMatch()
    
    task.ardSensor = ArduinoSensor("COM90")
    task.syringePump = SyringePump("COM91")
    task.stimDevice = Psycho(windowed=False)
    params = ParamsHeadfix()

    task.setUpStates()
    task.run()
    
