from __future__ import division
import sys
sys.path.append("..")


from ui.main_ui import *

class Resources():
    """
    Launch all the resources the UI says we need.
    Make dirs, start hardware devices, etc.
    """

    def __init__(self, mainUI):
        self.mainUI = mainUI  # type: MainUI

        #file path setup
        self.set_up_paths()
        print "saving files to " + self.experimentPath

        #Logging
        self.mainLog = Log(self.logPath)

        #Saving of objects e.g. trials to .pkl
        if do_saving:
            self.outFilePathPkl = self.experimentPath + self.dateStr + "_" + self.sessionStr + "_trials_and_params.pkl"

        #Camera
        self.cameraReader = None
        self.start_camera()

        #UI -- requires some fancy threading stuff, so it needs to go last. Continues into _ui_setup.
        self.tracer = None
        self.start_tracer()

        self.interactUI = None
        self.interactUI = interact.InteractUI(task=self)

        self.run()

    def start_camera(self):
        print 'Recording video to ' + self.vidPath
        self.cameraReader = CameraReader(self.shrew.cameraID, self.vidPath, self.shrew.mame)
        self.cameraReader.startReadThread()

    def start_tracer(self):
        self.tracer = tracer.Tracer()

        #add "lick" and "tap" plots to the UI
        self.tracer.sig_add_trace.emit("Lick")
        self.tracer.sig_add_trace.emit("Tap")

        #Define thresholds on the tracer
        self.tracer.sig_set_threshold.emit("Lick", self.ardSensor.lickThreshold)
        self.tracer.sig_set_threshold.emit("Tap", self.ardSensor.tapThreshold)

    def initialize_daq(self):
        try:
            print "Initializing DAQ..."
            #The import takes several seconds so it's best to do it
            #in the midst of the code, rather than at the top of the file.
            from devices.daq import MccDaq
            sys.stdout.flush()
            self.daq = MccDaq()
        except:
            print "Warning: No Measurement Computing DAQ available."


    def set_up_paths():
        """
        Makes a dir to hold the training session data.
        Composes paths for the logfile, settings, results, recorded video, etc.
        """
        cwd = os.getcwd()
        m = re.search("(.*Documents)", cwd)
        self.shrewPath = m.group(1) + os.sep + "ShrewData" + os.sep + self.shrew.name + os.sep

        self.dateStr = str(datetime.date.today())
        self.sessionStr = None
        if not os.path.exists(self.shrewPath + self.dateStr + os.sep):
            os.makedirs(self.shrewPath +  self.dateStr + os.sep)
        for i in range(1,10000):
            self.sessionStr = str(i).zfill(4)
            p = self.shrewPath + self.dateStr + os.sep + self.sessionStr + os.sep
            if not os.path.exists(p):
                os.makedirs(p)
                self.experimentPath = p
                break

        self.experimentPath = self.experimentPath.replace("\\","/")
        self.logPath = self.experimentPath + self.dateStr + "_" + self.sessionStr + "_log.txt"
        self.vidPath = self.experimentPath + self.shrewDriver.sessionFileName + '.avi'
