from __future__ import division
import sys
sys.path.append("..")

from PyQt4 import QtCore, QtGui
from PyQt4 import uic
import _winreg as winreg

import time

#load the .ui files
Interact_class = uic.loadUiType("../ui/interact.ui")[0]

class InteractUI(QtGui.QMainWindow, Interact_class):

    #define signals that we will accept and use to update the UI
    sigTrialEnd = QtCore.pyqtSignal()

    def __init__(self, parent=None, task=None):
        #make Qt window
        QtGui.QMainWindow.__init__(self, parent)
        #self.setGeometry( 500 , 1300 , 400 , 200 )

        self.setupUi(self)

        #connect button actions
        self.btnFail.clicked.connect(self.btnFailClicked)
        self.btnStartTrial.clicked.connect(self.btnStartTrialClicked)
        self.btnReward.clicked.connect(self.btnRewardClicked)

        self.btnGratingSPlus.clicked.connect(self.btnGratingSPlusClicked)
        self.btnGratingSMinus.clicked.connect(self.btnGratingSMinusClicked)

        self.btnShowOrientation.clicked.connect(self.btnShowOrientationClicked)

        self.btnGrayScreen.clicked.connect(self.btnGrayScreenClicked)
        self.btnBlack.clicked.connect(self.btnBlackClicked)

        #connect incoming signals
        self.sigTrialEnd.connect(self.trialEnd)        

        #setup
        self.task = task

        self.show()

    # --- Controls --- #
    def btnFailClicked(self):
        self.task.ui_fail_task()

    def btnStartTrialClicked(self):
        self.task.ui_start_trial()

    def btnRewardClicked(self):
        self.task.ui_dispense(0.1)

    def trialEnd(self):
        print "trial end"
    
    # --- Screen Manipulation --- #
    def btnGrayScreenClicked(self):
        self.task.stimDevice.write("sx0 sy0")
        self.task.daq.send_stimcode(20)
        print "Set screen to gray"
        self.task.mainLog.write("Set screen to gray")

    def btnGratingSPlusClicked(self):
        self.task.stimDevice.write("sqr135 as sf0.25 tf0 jf3 ja0.25 px0 py0 sx999 sy999")
        print "Set screen to S+ grating (135)"
        self.task.mainLog.write("Set screen to S+ grating (135)")
        self.task.daq.send_stimcode(21)
        time.sleep(0.5) #sleeping on the UI thread, such hacks *shudder*
        self.task.stimDevice.write("sx0 sy0")
        self.task.daq.send_stimcode(20)
        
    def btnGratingSMinusClicked(self):
        self.task.stimDevice.write("sqr160 as sf0.25 tf0 jf3 ja0.25 px0 py0 sx999 sy999")
        print "Set screen to S- grating (160)"
        self.task.mainLog.write("Set screen to S- grating (160)")
        self.task.daq.send_stimcode(22)
        time.sleep(0.5) #sleeping on the UI thread, such hacks *shudder*
        self.task.stimDevice.write("sx0 sy0")
        self.task.daq.send_stimcode(20)

    def btnShowOrientationClicked(self):
        ori = float(self.txtOrientation.text())
        gratingStr = "sqr" + str(ori)
        self.task.stimDevice.write(gratingStr + " as sf0.25 tf0 jf3 ja0.25 px0 py0 sx999 sy999")
        msg = "Set screen to grating (" + str(gratingStr) + ")"
        print msg
        self.task.mainLog.write(msg)
        self.task.daq.send_stimcode(23)
        time.sleep(0.5) #sleeping on the UI thread, such hacks *shudder*
        self.task.stimDevice.write("sx0 sy0")
        self.task.daq.send_stimcode(20)

    def btnBlackClicked(self):
        self.task.stimDevice.write("ac pab px0 py0 sx12 sy12")
        print "Set screen to black timeout circle"
        self.task.daq.send_stimcode(23)
        self.task.mainLog.write("Set screen to black timeout circle")

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myWindow = InteractUI()
    app.exec_()
