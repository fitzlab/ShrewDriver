import time
import functools
import random
import sys
from collections import OrderedDict

sys.path.append('..')
from util.cond_event import CondEvent

from task import *

class ParamsNonMatch(Params):
    
    def __init__(self):
        super(ParamsNonMatch, self).__init__()
        self.reward_mL = 0.2
        self.reward_hard_mL = 0.3

        self.sMinusOrientations = []
        self.sPlusOrientations = []

        self.timingDelayMin = 1.0
        self.timingDelayMax = 1.75
    
        self.hintChance = 1.0
        self.hintBolus = 0.03

        self.hitBolus = 0.150
        self.correctRejectBolus = 0.250


class TrialNonMatch(Trial):
    """
    A new trial object is made for each trial, so randomization can happen here.
    """

    MATCH = "match"
    NONMATCH = "nonmatch"

    def __init__(self, params):
        super(TrialNonMatch, self).__init__()
        self.params = params

        #roll trial type
        self.trialType = self.MATCH
        if random.random() > 0.5:
            self.trialType = self.NONMATCH
            
        #roll hints
        self.hint = False
        if random.random() < self.params.hintChance:
            self.hint = True
        
        #roll oris and phases according to discrimination task
        if self.params.discriminationType == self.params.ORIENTATION_DISCRIMINATION:
            #oris
            oris = self.params.getNonMatchingPair(self.params.sMinusOrientations, self.params.sPlusOrientations)
            self.sMinusOri = oris[0]
            self.sPlusOri = oris[1]
            
            #phases
            self.phaseSample = round(random.random(), 2)
            self.phaseMatch = round(random.random(), 2)
            self.phaseNonMatch = round(random.random(), 2)
            self.phaseNonMatchFinal = round(random.random(), 2)
            
        elif self.params.discriminationType == self.params.PHASE_DISCRIMINATION:
            #not implemented yet, just a placeholder
            #oris
            self.sMinusOri = self.params.sMinusOrientations[0]
            self.sPlusOri = self.params.sPlusOrientations[0]
            
            #phases
            self.phaseSample = round(random.random(), 2)
            self.phaseMatch = round(random.random(), 2)
            self.phaseNonMatch = round(random.random(), 2)
            self.phaseNonMatchFinal = round(random.random(), 2)
            
        #timing delay
        self.timingDelay = random.uniform(self.params.timingDelayMin, self.params.timingDelayMax)     
    

class TaskNonMatch(Task):
    
    def __init__(self, shrew):
        super(TaskNonMatch, self).__init__(shrew)
        self.params = None
        self._initMode = None

        self.trial = None
        self.trialHistory = []

        self.daq = None
        self.initialize_daq()
        
    def run(self):
        self.finished = False #change to True to stop running

        self.changeState(self.states["Timeout"])    
           
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
        self.states["TimingDelay"] = State()
        self.states["Sample"] = State()
        self.states["MemoryDelay"] = State()
        self.states["NonMatch"] = State()
        self.states["NonMatchResponse"] = State()
        self.states["Match"] = State()
        self.states["MatchResponse"] = State()
        self.states["NonMatchFinal"] = State()
        self.states["NonMatchFinalResponse"] = State()
        
        #make functions for changing to each state        
        self.changeTo = {}
        for key in self.states.keys():
            self.changeTo[key] = functools.partial(self.changeState, self.states[key])
            self.states[key].name = key  #tell each state what its name is
            
        #Timeout
        self.states["Timeout"].duration = 1
        self.states["Timeout"].actions.append( CondEvent([self.ardSensor.isNotLicking, self.ardSensor.isNotTapping, self.states["Timeout"].isDone], self.changeTo["Init"], "stopTapping") )    
        #self.states["Timeout"].actions.append( CondEvent([self.ardSensor.isNotTapping, self.states["Timeout"].isDone], self.changeTo["Init"], "stopTapping") )    
        
        #Init
        self.states["Init"].duration = None
        self.states["Init"].actions.append( CondEvent([self.states["Init"].isDone], self.changeTo["TimingDelay"], "done") )
        
        #TimingDelay
        self.states["TimingDelay"].duration = None
        self.states["TimingDelay"].actions.append( CondEvent([self.states["TimingDelay"].isDone], self.changeTo["Sample"], "done") )
        
        #Sample
        self.states["Sample"].duration = 0.5
        self.states["Sample"].actions.append( CondEvent([self.states["Sample"].isDone], self.changeTo["MemoryDelay"], "done") )

        #MemoryDelay
        self.states["MemoryDelay"].duration = 1
        self.states["MemoryDelay"].actions.append( CondEvent([self.states["MemoryDelay"].isDone, self.isMatchTrial], self.changeTo["Match"], "done") )
        self.states["MemoryDelay"].actions.append( CondEvent([self.states["MemoryDelay"].isDone, self.isNonMatchTrial], self.changeTo["NonMatch"], "done") )
        
        #Match
        self.states["Match"].duration = 0.5
        self.states["Match"].actions.append( CondEvent([self.states["Match"].isDone], self.changeTo["MatchResponse"], "done") )

        #MatchResponse        
        self.states["MatchResponse"].duration = 1
        self.states["MatchResponse"].actions.append( CondEvent([self.ardSensor.isLicking], self.falseAlarm, "falseAlarm") )
        self.states["MatchResponse"].actions.append( CondEvent([self.states["MatchResponse"].isDone], self.changeTo["NonMatchFinal"], "done") )
        
        #NonMatch
        self.states["NonMatch"].duration = 0.5
        self.states["NonMatch"].actions.append( CondEvent([self.states["NonMatch"].isDone], [self.changeTo["NonMatchResponse"], self.doHint], "done") )
        
        #NonMatchResponse
        self.states["NonMatchResponse"].duration = 1
        self.states["NonMatchResponse"].actions.append( CondEvent([self.ardSensor.isLicking], self.hit, "hit") )
        self.states["NonMatchResponse"].actions.append( CondEvent([self.states["NonMatchResponse"].isDone], self.miss, "miss") )

        #NonMatchFinal
        self.states["NonMatchFinal"].duration = 0.5
        self.states["NonMatchFinal"].actions.append( CondEvent([self.states["NonMatchFinal"].isDone], [self.changeTo["NonMatchFinalResponse"], self.doHint], "done") )
        
        #NonMatchFinalResponse
        self.states["NonMatchFinalResponse"].duration = 1
        self.states["NonMatchFinalResponse"].actions.append( CondEvent([self.ardSensor.isLicking], self.correctReject, "correctReject") )
        self.states["NonMatchFinalResponse"].actions.append( CondEvent([self.states["NonMatchFinalResponse"].isDone], self.taskFail, "noResponseFail") )

        #set up daq commands for each state
        for i,key in enumerate(self.states.keys()):
            self.states[key].stimcode = i        

        #Add task fails to most states for licking
        for key in self.states.keys():
            if key in ("TimingDelay", "Sample", "MemoryDelay", "Match", "NonMatch", "NonMatchFinal"):
                self.states[key].actions.append( CondEvent([self.ardSensor.isLicking], self.taskFail, "lickFail") )    
                #pass
                
    def newTrial(self):
        if self.trial is not None:
            self.trialHistory.append(self.trial)
            self.mainLog.write("Trial result: " + self.trial.result)
        self.trial = TrialNonMatch(self.params)        
        self.states["TimingDelay"].duration = self.trial.timingDelay

    def startTrial(self):
        """Triggered by UI. Changes state from Timeout or Init to the first state in the trial."""
        if not hasattr(self, "currentState"):
            #possible if user presses it before task loads all the way
            return
        if self.currentState == self.states["Timeout"] or self.currentState == self.states["Init"]:
            self.changeTo["TimingDelay"]()
        else:
            print "didn't change state. Current state is " + str(self.currentState)

    def changeState(self, newState):
        t = time.time()
        if hasattr(self, "currentState") and self.currentState is not None:
            self.currentState.endTime = t
            
            #We need to save the state in a picklable format
            #This requires removing all the actions, since those are 
            #functions and thus break pickling.
            statePicklable = copy.copy(self.currentState)
            statePicklable.actions = []
            self.trial.stateHistory.append(statePicklable)            

        
        #OK, start making the new state
        newState.startTime = t
        
        if newState.name == "Timeout":
            self.newTrial()
            self.save_data()
        

        self.mainLog.write("State changed to " + newState.name)
        print "State changed to " + newState.name
        
        self.currentState = newState
        
        
        #begin new state
        self.stateStart = time.time()
        
        #build screen command, including grating orientation and phase if needed
        oriCmd = ""
        phaseCmd = ""
        if newState.name == "Sample":
            oriCmd = "sqr" + str(self.trial.sMinusOri) + " "
            phaseCmd = "ph" + str(self.trial.phaseSample) + " "
        elif newState.name == "Match":
            oriCmd = "sqr" + str(self.trial.sMinusOri) + " "
            phaseCmd = "ph" + str(self.trial.phaseMatch) + " "
        elif newState.name == "NonMatch":
            oriCmd = "sqr" + str(self.trial.sPlusOri) + " "
            phaseCmd = "ph" + str(self.trial.phaseNonMatch)
        elif newState.name == "NonMatchFinal" :
            oriCmd = "sqr" + str(self.trial.sPlusOri) + " "
            phaseCmd = "ph" + str(self.trial.phaseNonMatchFinal) + " "
    
        self.stimDevice.write(oriCmd + phaseCmd + self.currentState.screenCommand)

        if self.daq is not None:
            self.daq.send_stimcode(self.currentState.stimcode)
            
        
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
                    self.states[key].actions.append( CondEvent([self.ardSensor.isNotInIR], self.taskFail, Task.INIT_IR) )        
            
        #initTap
        if self._initMode == Task.INIT_TAP:
            for key in self.states.keys():
                if key == "Init":
                    self.states[key].actions.append( CondEvent([self.ardSensor.isTapping], self.changeTo["TimingDelay"], Task.INIT_TAP) )        

    def isGuaranteedSPlus(self):
        return self.guaranteedSPlus            
    
    def isNotGuaranteedSPlus(self):
        return not self.guaranteedSPlus            

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
    
