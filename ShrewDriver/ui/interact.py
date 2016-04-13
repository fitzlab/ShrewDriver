from __future__ import division
import sys
sys.path.append("..")

from PyQt4 import QtCore, QtGui
from PyQt4 import uic
import _winreg as winreg
from constants.task_constants import *

import time

#load the .ui files
Interact_class = uic.loadUiType("ui/interact.ui")[0]

class InteractUI(QtGui.QMainWindow, Interact_class):

    #define signals that we will accept and use to update the UI
    sigTrialEnd = QtCore.pyqtSignal()

    def __init__(self, parent=None, task=None):
        #make Qt window
        QtGui.QMainWindow.__init__(self, parent)
        #self.setGeometry( 500 , 1300 , 400 , 200 )

        self.setupUi(self)

        #--- button actions ---#
        # shrew feedback
        self.btnGiveReward.clicked.connect(self.btn_give_reward_clicked)
        self.btnAirPuff.clicked.connect(self.btn_air_puff_clicked)

        # task manipulation
        self.btnTaskFail.clicked.connect(self.btn_task_fail_clicked)
        self.btnStartTrial.clicked.connect(self.btn_start_trial_clicked)

        self.btnShowNow.clicked.connect(self.btn_show_now_clicked)
        self.btnReplaceNext.clicked.connect(self.btn_replace_next_clicked)

        # screen manipulation
        self.btnBlack.clicked.connect(self.btn_black_clicked)
        self.btnGrayScreen.clicked.connect(self.btn_gray_screen_clicked)

        self.btnSPlusGrating.clicked.connect(self.btn_splus_grating_clicked)
        self.btnSMinusGrating.clicked.connect(self.btn_sminus_grating_clicked)

        self.btnRunStimCommand.clicked.connect(self.btn_run_stim_command_clicked)


        #setup
        self.task = task

        self.show()


    #--- shrew feedback ---#
    def btn_give_reward_clicked(self):
        self.task.training.sendStimcode(STIMCODE_REWARD_GIVEN)
        rewardAmount = float(str(self.txtRewardSize.getText()))
        self.task.ui_dispense(rewardAmount)

    def btn_air_puff_clicked(self):
        self.task.training.sendStimcode(STIMCODE_AIR_PUFF)
        pass

    #--- task manipulation ---#
    def btn_task_fail_clicked(self):
        self.task.ui_fail_task()

    def btn_start_trial_clicked(self):
        self.task.ui_start_trial()

    def btn_show_now_clicked(self):
        pass

    def btn_replace_next_clicked(self):
        pass

    #--- screen manipulation ---#
    def btn_black_clicked(self):
        pass

    def btn_gray_screen_clicked(self):
        pass

    def btn_splus_grating_clicked(self):
        pass

    def btn_sminus_grating_clicked(self):
        pass

    def btn_run_stim_command_clicked(self):
        pass


    #--- Old Stuff ---#
    
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
