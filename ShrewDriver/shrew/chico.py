"""Contains at least one function that defines a shrew's task and devices."""

import sys
sys.path.append("..")


class ChicoARC():
    
    def __init__(self):
        self.name = "Chico"
        self.ardSensorPort = "COM10"
        self.syringePort = "COM11"
        self.stimbotPort = "COM12"
        self.stimDevice = None
        self.cameraID = 5

        self.screenDist = 25
        
class ChicoUpstairs():
    
    def __init__(self):
        self.name = "Chico"
        self.ardSensorPort = "COM100"
        self.syringePort = "COM101"
        self.stimbotPort = None
        self.stimDevice = Psycho(windowed=False)
        self.cameraID = 5

        self.screenDist = 25

'''
def chico_headfix():
    shrew = ChicoUpstairs()
    task = TaskHeadfix(shrew)
    
    #params
    params = ParamsHeadfix()
    params.reward_mL = 0.2
    task.params = params

    #screen commands 
    task.setUpStates()
    task.initMode = Task.INIT_AUTO

    #ready to go
    task.start(do_ui=True, do_camera=False, do_logging=True)

def chico_nonmatch():

    shrew = ChicoUpstairs()
    task = TaskNonMatch(shrew)

    #params
    params = ParamsNonMatch()
    params.sPlusOrientations = [135]
    params.sMinusOrientations = [160]

    params.hintChance = 0.0 #<--- Decreased from 0.25 to 0 on Jan. 15 at Val's advice, since Chico's becoming too hint dependent.
    params.hintBolus = 0.050

    params.hitBolus = 0.300
    params.correctRejectBolus = 0.400

    task.params = params

    #screen commands 
    task.setUpStates()
    task.states["Timeout"].screenCommand = "ac pab px0 py0 sx12 sy12"
    task.states["Init"].screenCommand = "ac paw px0 py0 sx12 sy12"
    task.states["TimingDelay"].screenCommand = "sx0 sy0"
    task.states["Sample"].screenCommand = "as sf0.25 tf0 jf3 ja0.25 px0 py0 sx999 sy999"
    task.states["MemoryDelay"].screenCommand = "sx0 sy0"
    task.states["NonMatch"].screenCommand = "as sf0.25 tf0 jf3 ja0.25 px0 py0 sx999 sy999"
    task.states["NonMatchResponse"].screenCommand = "sx0 sy0"
    task.states["Match"].screenCommand = "as sf0.25 tf0 jf3 ja0.25 px0 py0 sx999 sy999"
    task.states["MatchResponse"].screenCommand = "sx0 sy0"
    task.states["NonMatchFinal"].screenCommand = "as sf0.25 tf0 jf3 ja0.25 px0 py0 sx999 sy999"
    task.states["NonMatchFinalResponse"].screenCommand = "sx0 sy0"
    
    task.initMode = task.INIT_TAP
    
    #ready to go    
    task.start(do_ui=True, do_camera=False, do_logging=True)

if __name__ == "__main__":
    chico_nonmatch()
    
   '''