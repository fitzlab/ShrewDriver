from __future__ import division
from collections import deque
import time
import threading
import re 
import sys
import subprocess
import os


from psycho_textures import circleGaussianFade, circleLinearFade

class Psycho():
    """
    Provides an easy interface to PsychoSubproc, which is what actually does all the work. 
    Never call PsychoSubproc() directly, use Psycho() instead.
    """
    def __init__(self, *args, **kwargs):
        thisfile = os.path.realpath(__file__)
        argStr = str(kwargs)

        self.logFile = None
        if "logFilePath" in kwargs:
            self.logFile = open(kwargs[logFilePath], 'w')
            
        print "Launching PsychoPy window..."
        sys.stdout.flush()        
        self.proc = subprocess.Popen("python " + thisfile + " " + argStr, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.proc.stdout.readline() #wait for psychopy to confirm that it's started

    def write(self, s):
        self.proc.stdin.write(s + "\n")        
        if self.logFile:
            t = time.time()
            
    def close(self):
        pass
    
    def getUpdates(self):
        pass

class PsychoSubproc():
    '''
    Renders stimbot commands in a PsychoPy window.
    
    PsychoPy runs inside a subprocess, and commands to the PsychoPy process are sent through pipes.
    This allows PsychoPy to run completely independent of the rest of ShrewDriver. Gets around the GIL, 
    keeping other operations (e.g. camera updates, disk writes) from affecting framerate.

    Thus, you shouldn't call this ever. Just call Psycho() instead.
    '''
    
    def __init__(self, screen=0, windowed=True):
        #stim params
        self.tf = 0
        self.windowed = windowed
        self.gratingStartTime = 0
        self.jitterAmount = 0
        self.jitterFrequency = 0
        self.phaseAtStart = 0
        
        self.cmds = deque()

        #make slots for command saving
        self.savedCommands = [""] * 100

        #initialize masks
        self.gaussianMask = circleGaussianFade(0.8)
        #self.linearMask = circleLinearFade(0.8) #unused

        #start render thread
        print "Starting PsychoPy window..."
        thread = threading.Thread(target=self.renderThreadFcn)
        thread.daemon = True
        thread.start()   
        
        #stim state variables
        self.drawPhotodiodeStim = True
        self.drawGrating = True
        self.drawPatch = False
    
        #allow plenty of time for window to start up
        time.sleep(4)
        
    def updatePhase(self):
        #called before grating appears, and again on each flip
        #updates grating's phase according to phase, tf, and jitter commands
        elapsed = time.time() - self.gratingStartTime
        tfOffset = elapsed * self.tf

        jitterPhase = (elapsed * self.jitterFrequency) % 1
        jitterOffset = jitterPhase
        if jitterOffset < 0.5:
            jitterOffset = 1-jitterOffset

        jitterOffset *= self.jitterAmount*2

        newPhase = self.phaseAtStart + tfOffset + jitterOffset
        self.grating.setPhase(newPhase)
        
    def renderThreadFcn(self):
        ''' Makes a PsychoPy window and begins listening for commands '''

        #setup must be done in same thread as rendering
        from psychopy import visual, logging, core, filters, event, monitors

        self.mon = monitors.Monitor('StimMonitor')
        self.mon.setDistance(25)
        self.mon.setSizePix([1920,1080])
        self.mon.setWidth(51)
        res = [1920,1080]
        if self.windowed:
            res = [800,600]
            
        #make window
        self.win = visual.Window(size=res,monitor=self.mon,fullscr=(not self.windowed),screen=1)
        
        #stimulus
        self.grating = visual.GratingStim(self.win, tex="sqr", mask="gauss", units="deg", size=(30,30), sf=0.05, ori=2, interpolate=True)
        self.drawGrating = True

        self.patch = visual.ImageStim(self.win, color=(0.0, 0.0, 0.0), units="deg", mask="circle", size=(50,50), texRes=1024)
        self.drawPatch = False
        
        #photodiode stim
        photodiodeStimPos = (-self.mon.getSizePix()[0]/2, self.mon.getSizePix()[1]/2)
        self.photodiodeStim = visual.ImageStim(self.win, color=(-1.0, -1.0, -1.0), units="pix", pos=photodiodeStimPos, size=(200,200))
        self.drawPhotodiodeStim = True #will be manually drawn on top of whatever stim is up
        
        #render loop
        timeBetweenFrames = 0.008
        while True:
            #update window
            self.win.flip()
            t0 = time.time()
            
            #read commands
            self.doCommands()

            #update stim phase based on jitter / temporal frequency
            self.updatePhase()
            
            #update photodiode stim
            self.updatePhotodiodeStim()
            
            #draw stims
            if self.drawPatch:
                self.patch.draw()
            if self.drawGrating:
                self.grating.draw()
            if self.drawPhotodiodeStim:
                #must draw this last so it's on top
                self.photodiodeStim.draw()

            elapsed = time.time()-t0
            #sleep for half the time remaining until the next frame
            sleepTime = max((timeBetweenFrames-elapsed)/2, 0.005)
            time.sleep(sleepTime) 

    def updatePhotodiodeStim(self):
        # Photodiode stim is solid white when no grating is displayed.
        # At the start of a grating, it goes black.
        # It then oscillates between gray and black while as long as the grating is displayed.
        if self.drawGrating and self.grating.size[0] > 0 and self.grating.size[1] > 0:
            if self.photodiodeStim.color[0] == -1.0:
                self.photodiodeStim.setColor((0.0,0.0,0.0))
            else:
                self.photodiodeStim.setColor((-1.0,-1.0,-1.0))
        else:
            self.photodiodeStim.setColor((1.0,1.0,1.0))
            

    def write(self, cmdStr):  
        self.cmds.append(cmdStr)

    def doCommand(self, cmd, number=None):

        #load existing
        if cmd == "load":
            self.commands.append(self.savedCommands[number])
            self.doCommands()

        #configuration
        if cmd == "screendist":
            print "setting dist to " + str(number)
            self.mon.setDistance(number)
            
        #textures
        elif cmd == "sin":
            self.grating.tex = "sin"
            self.grating.ori = 90+number
            self.showGrating()
        elif cmd == "sqr":
            self.grating.tex = "sqr"
            self.grating.ori = 90+number
            self.showGrating()

        #colors. Recall that -1 is black, 0 is gray, 1 is white in PsychoPy.
        elif cmd == "pab": #black
            self.patch.setColor((-1.0, -1.0, -1.0))
            self.showPatch()
        elif cmd == "paw": #white
            self.patch.setColor((1.0, 1.0, 1.0))
            self.showPatch()
        elif cmd == "pag": #gray
            self.patch.setColor((0.0, 0.0, 0.0))
            self.showPatch()
        elif cmd == "par": #red
            self.patch.setColor((1.0, 0.0, 0.0))
            self.showPatch()
        elif cmd == "pae": #green
            self.patch.setColor((0.0, 1.0, 0.0))
            self.showPatch()
        elif cmd == "pau": #blue
            self.patch.setColor((0.0, 0.0, 1.0))
            self.showPatch()
        elif cmd == "pac": #cyan
            self.patch.setColor((0.0, 1.0, 1.0))
            self.showPatch()
        elif cmd == "pay": #yellow
            self.patch.setColor((1.0, 1.0, 0.0))
            self.showPatch()
        elif cmd == "pam": #magenta
            self.patch.setColor((1.0, 0.0, 1.0))
            self.showPatch()
        
        #position
        elif cmd == "px":
            self.grating.setPos([number, self.grating.pos[1]])
            self.patch.setPos([number, self.patch.pos[1]])
        elif cmd == "py":
            self.grating.setPos([self.grating.pos[0], number])
            self.patch.setPos([self.patch.pos[0], number])

        #size
        elif cmd == "sx":
            self.grating.setSize([number, self.grating.size[1]])
            self.patch.setSize([number, self.patch.size[1]])
        elif cmd == "sy":
            self.grating.setSize([self.grating.size[0], number])
            self.patch.setSize([self.patch.size[0], number])

        #aperture
        elif cmd == "ac":
            self.grating.setMask("circle")
        elif cmd == "ag":
            self.grating.setMask("gauss")
        
        #aperture todo
        elif cmd == "as": #square
            self.grating.setMask(None)
        elif cmd == "acgf": #circle, gauss fade
            self.grating.setMask(self.gaussianMask)
        elif cmd == "aclf": #circle, linear fade
            raise NotImplementedError
            #self.grating.setMask(self.linearMask) #unused, not worth waiting for

        #grating funtimes
        elif cmd == "sf":
            self.grating.setSF(number)
        elif cmd == "tf":
            self.tf = number
        elif cmd == "ph":
            self.phaseAtStart = number
        elif cmd == "gc":
            self.grating.setContrast(number)
        elif cmd == "ja":
            self.jitterAmount = number
        elif cmd == "jf":
            self.jitterFrequency = number

    def doCommands(self):
        #splits command string into tokens and executes each one
        
        cmdStr = ""
        if len(self.cmds) > 0:
            cmdStr = self.cmds.popleft()
        if not cmdStr:
            return

        toks = cmdStr.rstrip().split()
        for t in toks:
            m = re.search("([a-z|A-Z]*)(\-?\d*\.?\d*)", t)
            if m is None:
                continue
            
            if m.group(1) == "" and m.group(2) != "":  
                #load saved command and run it
                number = int(m.group(2))
                self.cmds.append(self.savedCommands[number])
                
            else:
                #parse token
                cmd = m.group(1)
                number = None
                if len(m.group(2)) > 0:
                    number = float(m.group(2))
                
                #handle special case of "save". "save" must be at the beginning of saved command.
                if cmd == "save":
                    remainder = (" ").join(toks[1:])
                    assert "save" not in remainder #avoid infinite loop
                    self.savedCommands[int(number)] = remainder
                    break
                else:
                    #do the command
                    self.doCommand(cmd, number)
                    
    def showPatch(self):
        self.drawGrating = False
        self.drawPatch = True

    def showGrating(self):
        self.drawGrating = True
        self.drawPatch = False
        self.gratingStartTime = time.time()



class NoRender():
    """Use this class when you want no stim display, nice for testing"""
    def __init__(self):
        pass

    def write(self, s):
        pass


if __name__ == "__main__":
    if len(sys.argv) == 1:
        #Demonstration
        pw = Psycho(windowed=False)
    
        cmds = ["as pab sx999 sy999",
                "save0 ac sf2 ph0.76",
                "save1 sf0.5 sx30 sy30 as",
                "0 sqr45 ph0.76",
                "1",
                "tf1.0",
                "tf0",
                "ph0.25",
                "ph0.5 gc0.5",
                "ph0.75",
                "sx3 sy3 acgf sqr45 ja1.0 jf1.0"]
    
        for cmd in cmds:
            time.sleep(1.5) 
            print cmd
            pw.write(cmd)
            
            
        cmds = ["paw", "pab"]
        pw.write("as pab sx30 sy30")
        while True:
            for cmd in cmds:
                pw.write(cmd)
            
        #don't close pipe until parent has finished reading, or error will occur
        time.sleep(10.0)
        
    else:
        #This is the child process that Psycho runs in.

        #parse kwargs. Will have to change this if you add any more args actually.
        kwargStr = "".join(sys.argv[1:])
        w = False
        if "True" in kwargStr:
            w = True
        p = PsychoSubproc(windowed=w)
        
        #send back a "ready" confirmation to main process
        print "PsychoPy ready!"
        sys.stdout.flush()
        
        #listen to stdin for commands, pass them to Psycho
        while True:
            s = raw_input()
            p.write(s.rstrip() + "\n") #ensure newline on writes
       
