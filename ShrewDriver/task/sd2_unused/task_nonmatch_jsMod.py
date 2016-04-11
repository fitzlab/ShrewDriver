import time
import functools
import random
import sys
import itertools

sys.path.append('..')
from util.cause_effect import CauseEffect

from task import *

class ParamsNonMatch():

    def __init__(self):
        self.reward_mL = 0.2
        self.reward_hard_mL = 0.3

        self.sMinusOrientations = []
        self.sPlusOrientations = []

        self.timingDelayMin = 0.5
        self.timingDelayMax = 1.25
    
        self.hintChance = 0.5
        self.hintBolus = 0.03

        self.hitBolus = 0.150
        self.correctRejectBolus = 0.250

    def getOrientations(self):
        """returns a tuple (sPlus, sMinus) where sPlus != sMinus"""
        all_pairs = list(itertools.product(self.sMinusOrientations, self.sPlusOrientations))
        distinct_pairs = []
        for pair in all_pairs:
            #orientations considered equal if within 0.1 degrees. Prevents float errors.
            if abs(pair[0] - pair[1]) > 0.1:
                distinct_pairs.append(pair)

        return random.choice(distinct_pairs)

class TrialNonMatch():
    """
    A new trial object is made for each trial, so randomization can happen here.
    """

    MATCH = "match"
    NONMATCH = "nonmatch"

    def __init__(self, params):
        self.params = params

        self.trialType = self.MATCH
        if random.random() > 0.5:
            self.trialType = self.NONMATCH

        self.hint = False
        if random.random() < self.params.hintChance:
            self.hint = True

        oris = params.getOrientations()
        self.sMinus = oris[0]
        self.sPlus = oris[1]

        self.timingDelay = random.uniform(self.params.timingDelayMin, self.params.timingDelayMax)     
    

class TaskNonMatch(Task):
    
    def __init__(self, shrew):
        super(TaskNonMatch, self).__init__(shrew)
        self.params = None

        self._initMode = None

        self.trial = None
        self.trialHistory = []
        
    def run(self):
        self.finished = False #change to True to stop running

        self.changeState(self.states["Timeout"])    
        
        li = 0
        ti = 0    
        while not self.finished:
            updates = self.ardSensor.checkSensors()
            self.currentState.checkActions()

            if self.tracer is not None:
                #update tracer with new sensor information
                for update in updates:
                    (data, t) = update
                    toks = data.rstrip().split()
                    if len(toks) < 2 or not toks[1].isdigit:
                        continue
                    try:
                        level = int(toks[1])
                        if toks[0] == "L":
                            self.tracer.sig_add_data.emit("Lick", li, level)
                            li += 1
                        if toks[0] == "T":
                            self.tracer.sig_add_data.emit("Tap", ti, level)
                            ti += 1
                    except:
                        continue                

            time.sleep(0.01) #allow other threads to run, e.g. psychopy
     
   
    def setUpStates(self):
        #declare all states
        self.states = {}
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
        self.states["Timeout"].screenCommand = "tone5"
        self.states["Timeout"].duration = 1
        self.states["Timeout"].actions.append( CauseEffect([self.ardSensor.isNotTapping, self.states["Timeout"].isDone], self.changeTo["Init"], "stopTapping") )     
        
        #PreInit
        self.states["PreInit"].screenCommand = ""
        self.states["PreInit"].duration = None
        self.states["PreInit"].actions.append( CauseEffect([self.states["PreInit"].isDone], self.changeTo["Init"], "done") ) 
        
        #Init
        self.states["Init"].screenCommand = ""
        self.states["Init"].duration = None
        self.states["Init"].actions.append( CauseEffect([self.states["Init"].isDone], self.changeTo["TimingDelay"], "done") )
        
        #TimingDelay
        self.states["TimingDelay"].screenCommand = ""
        self.states["TimingDelay"].duration = None
        self.states["TimingDelay"].actions.append( CauseEffect([self.states["TimingDelay"].isDone], self.changeTo["Sample"], "done") )
        
        #Sample
        self.states["Sample"].screenCommand = ""
        self.states["Sample"].duration = 1
        self.states["Sample"].actions.append( CauseEffect([self.states["Sample"].isDone], self.changeTo["MemoryDelay"], "done") )

        #MemoryDelay
        self.states["MemoryDelay"].screenCommand = ""
        self.states["MemoryDelay"].duration = 1
        self.states["MemoryDelay"].actions.append( CauseEffect([self.states["MemoryDelay"].isDone, self.isMatchTrial], self.changeTo["Match"], "done") )
        self.states["MemoryDelay"].actions.append( CauseEffect([self.states["MemoryDelay"].isDone, self.isNonMatchTrial], self.changeTo["NonMatch"], "done") )
        
        #Match
        self.states["Match"].screenCommand = ""   
        self.states["Match"].duration = 1
        self.states["Match"].actions.append( CauseEffect([self.states["Match"].isDone], self.changeTo["MatchResponse"], "done") )

        #MatchResponse
        self.states["MatchResponse"].screenCommand = ""           
        self.states["MatchResponse"].duration = 1
        self.states["MatchResponse"].actions.append( CauseEffect([self.ardSensor.isLicking], self.falseAlarm, "falseAlarm") )
        self.states["MatchResponse"].actions.append( CauseEffect([self.states["MatchResponse"].isDone], self.changeTo["NonMatchFinal"], "done") )
        
        #NonMatch
        self.states["NonMatch"].screenCommand = ""
        self.states["NonMatch"].duration = 1
        self.states["NonMatch"].actions.append( CauseEffect([self.states["NonMatch"].isDone], [self.changeTo["NonMatchResponse"], self.doHint], "done") )
        
        #NonMatchResponse
        self.states["NonMatchResponse"].screenCommand = ""
        self.states["NonMatchResponse"].duration = 1
        self.states["NonMatchResponse"].actions.append( CauseEffect([self.ardSensor.isLicking], self.hit, "hit") )
        self.states["NonMatchResponse"].actions.append( CauseEffect([self.states["NonMatchResponse"].isDone], self.miss, "miss") )

        #NonMatchFinal
        self.states["NonMatchFinal"].screenCommand = ""
        self.states["NonMatchFinal"].duration = 1
        self.states["NonMatchFinal"].actions.append( CauseEffect([self.states["NonMatchFinal"].isDone], [self.changeTo["NonMatchFinalResponse"], self.doHint], "done") )
        
        #NonMatchFinalResponse
        self.states["NonMatchFinalResponse"].screenCommand = ""
        self.states["NonMatchFinalResponse"].duration = 1
        self.states["NonMatchFinalResponse"].actions.append( CauseEffect([self.ardSensor.isLicking], self.correctReject, "correctReject") )
        self.states["NonMatchFinalResponse"].actions.append( CauseEffect([self.states["NonMatchFinalResponse"].isDone], self.taskFail, "noResponseFail") )
        
        self.stateHistory = []

        #Add task fails to most states for licking
        for key in self.states.keys():
            if key in ("TimingDelay", "Sample", "MemoryDelay", "Match", "NonMatch", "NonMatchFinal"):
                pass
                #self.states[key].actions.append( CauseEffect([self.ardSensor.isLicking], self.taskFail, "lickFail") )    


    
    def newTrial(self):
        if self.trial is not None:
            self.trialHistory.append(self.trial)
            self.mainLog.write("Trial result: " + self.trial.result)
        self.trial = TrialNonMatch(self.params)        
        self.states["TimingDelay"].duration = self.trial.timingDelay

    def changeState(self, newState):
        if newState.name == "Timeout":
            self.newTrial()

        self.mainLog.write("State changed to " + newState.name)

        self.currentState = newState
        self.currentState.startTime = time.time()
        
        print "State changed to " + newState.name
        
        #any state specific conditionals, e.g. grating orientations, phases, or duration
        screenCommand = self.currentState.screenCommand
        
        #begin new state
        self.stateStart = time.time()
        
        if newState.name == "Sample" or newState.name == "Match":
            self.stimDevice.write("sqr" + str(self.trial.sMinus) + " " + screenCommand)
        elif newState.name == "NonMatch" or newState.name == "NonMatchFinal" :
            self.stimDevice.write("sqr" + str(self.trial.sPlus) + " " + screenCommand)
        else:
            self.stimDevice.write(screenCommand)
        
        
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
    
