from __future__ import division
import sys
sys.path.append("..")

import time
import re
import threading

import pyqtgraph as pg
from PyQt4.QtCore import * 
from PyQt4.QtGui import * 
from PyQt4 import QtCore
import numpy as np
import copy

from constants.graph_constants import *

class LivePlot(QWidget):
    
    #define signals that we will accept
    sigEvent = QtCore.pyqtSignal(str, float)
    sigUpdate = QtCore.pyqtSignal()

    def __init__(self, animalName):
        self.startTime = time.time()
        self.lastUpdate = 0

        #--- init plot ---#
        self.axis = TimeAxis(orientation='bottom')
        self.app = pg.mkQApp()
        self.vb = pg.ViewBox()
        self.pw = pg.PlotWidget(viewBox=self.vb, axisItems={'bottom': self.axis}, enableMenu=False, title="")
        self.pw.showAxis('left', False)
        
        self.pw.setXRange(0, 300)
        self.pw.setYRange(0, 10)
        self.pw.show()
        self.pw.setWindowTitle(animalName + " - Live Plot")
        
        self.pw.addLegend()

        #prevent scaling+scrolling in Y, and don't go into negative x
        self.vb.setLimits(xMin=0, yMin=0, yMax=10, minYRange=10, maxYRange=10)
        self.vb.autoRange()
        
        #--- init plot curves ---#
        numStates = 7
        
        self.rewardCurve = IntCurve(REWARD, 5, get_color(REWARD), 1, self.pw)
        self.hintCurve = IntCurve(HINT, 4, get_color(HINT), 1, self.pw)
        self.stateCurve = IntCurve(STATE, 3, get_color(STATE), numStates, self.pw)
        self.lickCurve = IntCurve(LICK, 2, get_color(LICK), 4, self.pw)
        self.tapCurve = IntCurve(TAP, 1, get_color(TAP), 4, self.pw)
        self.airCurve = IntCurve(AIR_PUFF, 0, get_color(AIR_PUFF), 1, self.pw)

        # trailing points needed to represent current state
        self.tapState = 0;
        self.lickState = 0;

        QWidget.__init__(self) 
        
        # Accept updates via signals. 
        # We have to do it via the Qt signals and slots system, because
        # we are using two threads, and Qt wants everything in one thread. 
        # So communication between threads must be done via signals, otherwise
        # things get weird (plot updates will be screwed up).
        self.sigEvent.connect(self.addEvent)
        self.sigUpdate.connect(self.update)
        
    def addEvent(self, eventType, timestamp):
        evtType = str(eventType) #convert from QString
        t = timestamp - self.startTime
        #print "GOT EVENT: " + evtType + " " + str(t)
        if evtType.startswith('Lx'):
            if len(evtType) > 2:
                magnitude = int(evtType[2])
                self.lickCurve.appendPoint(t,magnitude)
            else:
                self.lickCurve.appendPoint(t,4)
        if evtType == 'Lo':
            self.lickCurve.appendPoint(t,0)
        if evtType.startswith('Tx'):
            if len(evtType) > 2:
                magnitude = int(evtType[2])
                self.tapCurve.appendPoint(t,magnitude)
            else:
                self.tapCurve.appendPoint(t,4)
        if evtType == 'To':
            self.tapCurve.appendPoint(t,0)
        if evtType.startswith('State'):
            stateNumber = int(evtType[5:])
            self.stateCurve.appendPoint(t,stateNumber)
        if evtType == 'Puff':
            self.airCurve.appendPoint(t,1)
            self.airCurve.appendPoint(t+0.001,0)
        if evtType == 'RL':
            self.hintCurve.appendPoint(t,1)
            self.hintCurve.appendPoint(t+0.001,0)
        if evtType == 'RH':
            self.rewardCurve.appendPoint(t,1)
            self.rewardCurve.appendPoint(t+0.001,0)

        #ignore any other events
        super(LivePlot, self).repaint()


    def update(self, t=None):
        """Called periodically from training program.
        Updates each curve to show current state.
        t parameter is only used by test function below."""
        if t is None:
            #t is only defined for testing examples; normally it's the current time.
            t = time.time() - self.startTime
        if t - self.lastUpdate < 1:
            #update every 1s at most
            return

        self.lastUpdate = t

        for curve in [self.lickCurve, self.tapCurve, self.stateCurve, self.airCurve, self.rewardCurve, self.hintCurve]:
            curve.update(t)
        #self.repaint()
        super(LivePlot, self).repaint()
        
    def addTestPoints(self):
        self.startTime = 0
        self.addEvent("Lx1", 100)
        self.addEvent("Lo", 130)
        self.addEvent("Lx2", 500)
        self.addEvent("Lo", 530)
        self.addEvent("Lx3", 800)
        self.addEvent("Lo", 830)
        self.addEvent("Puff", 200)
        self.addEvent("Puff", 650)
        self.addEvent("Puff", 1200)
        self.addEvent("Puff", 2650)
        self.addEvent("Tx2", 200)
        self.addEvent("To", 220)
        self.addEvent("Tx3", 1200)
        self.addEvent("To", 1220)
        self.addEvent("Tx4", 1240)
        self.addEvent("To", 1280)
        self.addEvent("State0", 0)
        self.addEvent("State1", 500)
        self.addEvent("State2", 1000)
        self.addEvent("State3", 1500)
        self.addEvent("State4", 2000)
        self.addEvent("State5", 2500)
        self.addEvent("State6", 3000)
        self.addEvent("State7", 3500)
        self.addEvent("State0", 4000)
        self.addEvent("RL", 650)
        self.addEvent("RL", 1650)
        self.addEvent("RL", 3650)
        self.addEvent("RH", 700)
        self.addEvent("RH", 2700)

        self.update(t=5000)

class IntCurve:
    def __init__(self, name, index, color, yMax, pw):
        self.name = name
        self.yMin = index * 1.1  # specifies where the curve is vertically on the plot
        self.yMax = yMax  # yMax is the highest input value.

        self.x = [0]
        self.xBase = [0]
        self.y = [self.yMin]
        self.yBase = [self.yMin]

        self.state = 0
        
        self.yPrev = 0
        self.xPrev = 0
        
        # make curve on plotwidget 'pw'
        self.sig = pw.plot(pen=color, name=self.name)
        self.sig.setData(self.x, self.y)
        self.base = pw.plot(pen=color)
        self.base.setData(self.xBase,self.yBase)
        fill = pg.FillBetweenItem(self.base, self.sig, color)
        pw.addItem(fill)
        
    
    def appendPoint(self, xNew, yNew):
        """Display the latest point associated with this curve."""
        #add two points to make vertical line on curve (low-to-high or high-to-low)
        self.x.append(xNew)
        self.y.append(self.yPrev/self.yMax + self.yMin)
        self.x.append(xNew)
        self.y.append(yNew/self.yMax + self.yMin)
        
        #update base curve as well
        self.xBase.append(xNew)
        self.yBase.append(self.yMin)

        #save input point so we can interpret the next input
        self.xPrev = xNew
        self.yPrev = yNew

        #update drawn lines with new data
        self.sig.setData(self.x, self.y)
        self.base.setData(self.xBase, self.yBase)

    def update(self, t):
        """Called periodically with no event. Just updates this curve to show current state."""

        #add current state to a temporary point array
        self.xRender = copy.copy(self.x)
        self.xRenderBase = copy.copy(self.xBase)
        self.yRender = copy.copy(self.y)
        self.yRenderBase = copy.copy(self.yBase)

        self.xRender.append(t)
        self.xRenderBase.append(t)
        self.yRender.append(self.yPrev/self.yMax + self.yMin)
        self.yRenderBase.append(self.yMin)

        #render it
        self.sig.setData(self.xRender, self.yRender)
        self.base.setData(self.xRenderBase, self.yRenderBase)


def timestampToString(timestamp):
    timeStr = ''
    hours = int(timestamp / (60*60))
    if hours > 0:
        timestamp = timestamp - hours * (60*60)
        timeStr += str(hours) + ":"
    
    minutes = int(timestamp / (60))
    if minutes > 0 or hours > 0:
        timestamp = timestamp - minutes * (60)
        timeStr += str(minutes).zfill(2) + ":"
    
    seconds = int(timestamp)
    if seconds > 0 or minutes > 0 or hours > 0:
        timestamp = timestamp - seconds
        timeStr += str(seconds).zfill(2) + "."
    
    timeStr += str(int(timestamp*1000)).zfill(3)
    
    return timeStr

class TimeAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        strns = []
        for x in values:
            strns.append(timestampToString(x))
        return strns

if __name__ == '__main__':
    from pyqtgraph.Qt import QtGui, QtCore
    app = QtGui.QApplication(sys.argv)
    lp = LivePlot('AnimalName')
    lp.addTestPoints()
    QtGui.QApplication.instance().exec_()
