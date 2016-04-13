
"""Contains at least one function that defines a shrew's task and devices."""

def set_params(task):

    shrew = QueenUpstairs()
    task = TaskDiscrimination(shrew)

    self.stimDevice = None
    self.cameraID = 5

    self.screenDist = 25

    self.stimbotPort = None
    self.stimDevice = Psycho(windowed=False)
    self.cameraID = 5

    self.screenDist = 20

    params.sPlusOrientations = [135]
    params.sMinusOrientations = [160]

    params.hintChance = 0.0
    params.hintBolus = 0.05

    params.hitBolus = 0.350
    params.correctRejectBolus = 0.450

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


'''

'''