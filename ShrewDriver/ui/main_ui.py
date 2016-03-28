from __future__ import division

import os
import sys
import json
import threading
import traceback
import time
import win32clipboard

from PyQt4 import QtCore, QtGui, uic
import pyqtgraph as pg

from ui_graphs.graph_performance import GraphPerformance
from ui_graphs.graph_events import GraphEvents
from ui_graphs.graph_history import GraphHistory
from ui_graphs.graph_lick_times import GraphLickTimes

sys.path.append('../')
from devices.available import get_serial_ports, get_cameras
from shrew.shrew import get_animals, Shrew
from db import create_db_files

#load the .ui files
ShrewDriver_class = uic.loadUiType("ui/main_ui.ui")[0]

class MainUI(QtGui.QMainWindow, ShrewDriver_class):

    # #--- Signals to accept ---#
    # self.sig_add_data.connect(self._add_data)
    # self.sig_add_trace.connect(self._add_trace)
    # self.sig_set_threshold.connect(self._set_threshold)

    def __init__(self, parent=None):

        #pyqt setup
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        #current selections
        self.selectedAnimal = None  # type: Shrew
        self.selectedSession = None  # type: str
        self.selectedTask = None  # type: callable
        self.selectedConfig = None  # instance of a config class

        #UI sub-objects
        self.performancePlot = None
        self.historyPlot = None
        self.runPlot = None
        self.movieWidget = None

        #Graphs
        self.graphEvents = GraphEvents(self)
        self.graphPerformance = GraphPerformance(self)
        self.graphHistory = GraphHistory(self)
        self.graphLickTimes = GraphLickTimes(self)

        self.tabEventsLayout.addWidget(self.graphEvents.plot)
        self.tabPerformanceLayout.addWidget(self.graphPerformance.plot, 2, 0, 1, 4)
        self.tabLickTimesLayout.addWidget(self.graphLickTimes.gw, 4, 0, 1, 1)
        self.tabHistoryLayout.addWidget(self.graphHistory.plot, 2, 0, 1, 4)

        #button actions
        self.btnStartTask.clicked.connect(self.start_task)
        self.btnCopyResults.clicked.connect(self.copy_results)

        #checkbox actions
        self.chkDiscriminationRateHist.stateChanged.connect(self.graphHistory.update_checked)
        self.chkSPlusResponseRateHist.stateChanged.connect(self.graphHistory.update_checked)
        self.chkSMinusRejectRateHist.stateChanged.connect(self.graphHistory.update_checked)
        self.chkTaskErrorRateHist.stateChanged.connect(self.graphHistory.update_checked)

        self.chkTotalmLHist.stateChanged.connect(self.graphHistory.update_checked)
        self.chkmLPerHourHist.stateChanged.connect(self.graphHistory.update_checked)
        self.chkTrialsHist.stateChanged.connect(self.graphHistory.update_checked)
        self.chkTrainingDurationHist.stateChanged.connect(self.graphHistory.update_checked)

        self.chkDiscriminationRatePerf.stateChanged.connect(self.graphPerformance.update_checked)
        self.chkTaskErrorRatePerf.stateChanged.connect(self.graphPerformance.update_checked)
        self.chkTotalmLPerf.stateChanged.connect(self.graphPerformance.update_checked)
        self.chkTrialsPerHourPerf.stateChanged.connect(self.graphPerformance.update_checked)

        self.rdoHistogram.toggled.connect(self.graphLickTimes.update_checked)
        self.rdoTrialNumber.toggled.connect(self.graphLickTimes.update_checked)

        #combo box actions
        self.cmbAnimal.currentIndexChanged.connect(self.set_animal)
        self.cmbConfig.currentIndexChanged.connect(self.set_config)
        self.cmbTask.currentIndexChanged.connect(self.set_task)
        self.cmbSession.currentIndexChanged.connect(self.set_session)

        #populate devices, graphs, shrews, etc.
        self.cameras = get_cameras()
        self.serialPorts = get_serial_ports()
        self.animals = get_animals('./shrew')
        self.populate_ui()
        self.update_graphs()

        #used by task
        self.stopTask = True
        self.taskThread = None


    def populate_ui(self):
        """Fill in combo boxes and initialize graphs"""

        '''
        for camera in self.cameras:
            if "Video" in camera[0]:
                self.cmbCamera.addItem(camera[0])
        
        for serialPort in self.serialPorts:
            for serialCmb in [self.cmbSensors, self.cmbReward, self.cmbStimDevice]:
                serialCmb.addItem(serialPort.name)
        self.cmbStimDevice.addItem("PsychoPy")
        '''

        for a in self.animals:
            self.cmbAnimal.addItem(a.name.capitalize())
        self.set_animal()

    #--- Button callbacks ---#
    def start_task(self):

        if self.taskThread == None:  #no task is running, so start one
            """Calls the function of the selected task"""
            if self.selectedAnimal is None:
                print "Select an animal first!"
            if self.selectedConfig is None:
                print "Select a config first!"
            if self.selectedTask is None:
                print "Select a task first!"

            self.save_params()
            self.stopTask = False  # thread will stop when this turns true

            self.taskThread = threading.Thread(target=self.selectedTask, args=[self])
            self.taskThread.start()

            self.btnStartTask.setText("Stop Task")

        else:
            self.stopTask = True # will cause thread to stop
            self.btnStartTask.setText("Start Task")
            self.taskThread = None

    def refresh_sessions(self):
        self.cmbSession.clear()
        try:
            sessions = create_db_files.get_sessions_for_shrew(self.selectedAnimal.name)
            for s in reversed(sessions):
                self.cmbSession.addItem(s)
            self.cmbSession.setCurrentIndex(0)
        except Exception as e:
            print "Can't load db for animal: ", self.selectedAnimal.name
            print traceback.print_exc()


    def copy_results(self):
        """
        Copies results text to clipboard.
        Highlights all the text to make it look like the button did something.
        """

        #copy
        resultsText = str(self.txtResults.toPlainText())
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(resultsText)
        win32clipboard.CloseClipboard()

        #highlight
        cursor = self.txtResults.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(len(resultsText), QtGui.QTextCursor.KeepAnchor)
        self.txtResults.setTextCursor(cursor)

    def update_graphs(self):
        self.graphHistory.load_db()
        self.graphPerformance.load_db()
        self.graphEvents.load_db()
        self.graphLickTimes.load_db()

    #--- Combo box callbacks ---#
    def set_animal(self):
        for a in self.animals:
            if a.name.lower() == str(self.cmbAnimal.currentText()).lower():
                self.selectedAnimal = a  # type: Shrew
                self.setWindowTitle(self.selectedAnimal.name.capitalize() + " - ShrewDriver")

        # Show available configs and tasks for this animal
        self.cmbConfig.clear()
        for c in self.selectedAnimal.configs:
            self.cmbConfig.addItem(c.__name__)

        self.cmbTask.clear()
        for t in self.selectedAnimal.tasks:
            self.cmbTask.addItem(t.__name__)

        self.load_params()
        self.refresh_sessions()

    def set_config(self):
        for c in self.selectedAnimal.configs:
            if c.__name__.lower() == str(self.cmbConfig.currentText()).lower():
                self.selectedConfig = c()  # Will be an instance of the class, not the class itself

    def set_task(self):
        for t in self.selectedAnimal.tasks:
            if t.__name__.lower() == str(self.cmbTask.currentText()).lower():
                self.selectedTask = t

    def set_session(self):
        self.selectedSession = str(self.cmbSession.currentText())
        print "session set to ", self.selectedSession
        self.update_graphs()

    #--- Parameter saving ---#
    def get_settings_filepath(self):
        dataPath = "../../ShrewData/"
        if not os.path.isdir(dataPath):
            os.makedirs(dataPath)
        return dataPath + self.selectedAnimal.name + "_settings.txt"

    def set_combo_box(self, cbx, value):
        index = cbx.findText(str(value))
        cbx.setCurrentIndex(index)
        #print "setting " + value + " idx " + str(index)

    def save_params(self):
        """
        Called when task is started.
        Saves the previous config and task to a file.
        """
        d = {'selectedConfig':self.selectedConfig.__class__.__name__, 'selectedTask':self.selectedTask.__name__}
        with open(self.get_settings_filepath(), 'w') as fp:
            json.dump(d, fp)

    def load_params(self):
        """
        Called when animal is selected.
        Loads the previous config and task from the saved file, if possible.
        """
        if not os.path.isfile(self.get_settings_filepath()):
            return #no saved params

        with open(self.get_settings_filepath(), 'r') as fp:
            d = json.load(fp)  # type: dict
            for key in d.keys():
                if key == "selectedConfig":
                    self.set_combo_box(self.cmbConfig, d[key])
                if key == "selectedTask":
                    self.set_combo_box(self.cmbTask, d[key])
