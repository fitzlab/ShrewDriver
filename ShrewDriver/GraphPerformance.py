from __future__ import division

import time, re, sys, threading, random

import pyqtgraph as pg
from PyQt4.QtCore import * 
from PyQt4.QtGui import * 
from PyQt4 import QtCore
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore

sys.path.append("./util")
sys.path.append("./global")
from Constants import *

sys.path.append("./trial")
from Trial import Trial


class Aph(QWidget):

    #define signals that we will accept
    sigEvent = QtCore.pyqtSignal(str, float) 

    def __init__(self, animalName):
        self.startTime = time.time()
        
        
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
        
        QWidget.__init__(self) 
        
        # Accept updates via signals. 
        # We have to do it via the Qt signals and slots system, because
        # we are using two threads, and Qt wants everything in one thread. 
        # So communication between threads must be done via signals, otherwise
        # things get weird (plot updates will be screwed up).
        self.sigEvent.connect(self.addEvent)
        
        self.numToAverage = 20
        
    def addSession(self, trials):
        resultsBuffer = [False] * self.numToAverage
        numResults = 0
        points = []
        endTimes = []
        for t in trials:
            wasSuccess = False
            if t.result == Results.CORRECT_REJECT or t.result == Results.HIT:
                wasSuccess = True

            resultsBuffer[numResults % self.numToAverage] = wasSuccess
            
            if numResults > len(resultsBuffer):
                percentCorrect = reduce((lambda x,y: int(x)+int(y)), resultsBuffer) / len(resultsBuffer) * 100
                points.append(percentCorrect)
            
            numResults += 1

        super(LivePlot, self).repaint()
        super(LivePlot, self).setFocus()            

        self.rewardPoints = IntCurve('Reward', 5, [0,255,255], 1, self.pw)
        
        
        
    def addEvent(self, eventType, timestamp):
        evtType = str(eventType) #convert from QString
        t = timestamp - self.startTime
        #print "GOT EVENT: " + evtType + " " + str(t)
        if evtType == 'Ix':
            self.irPoints.appendPoint(t,1)
        if evtType == 'Io':
            self.irPoints.appendPoint(t,0)
        if evtType == 'Lx':
            self.lickPoints.appendPoint(t,1)
        if evtType == 'Lo':
            self.lickPoints.appendPoint(t,0)
        if evtType == 'Tx':
            self.tapPoints.appendPoint(t,1)
        if evtType == 'To':
            self.tapPoints.appendPoint(t,0)
        if evtType.startswith('State'):
            stateNumber = int(evtType[5:])
            self.statePoints.appendPoint(t,stateNumber)
        if evtType == 'RL':
            self.hintPoints.appendPoint(t,1)
            self.hintPoints.appendPoint(t+0.001,0)
        if evtType == 'RH':
            self.rewardPoints.appendPoint(t,1)
            self.rewardPoints.appendPoint(t+0.001,0)
        #ignore any other noise, e.g. "bolus" notifications
        
        super(LivePlot, self).repaint()
        super(LivePlot, self).setFocus()
        
    def addTestPoints(self):
        self.startTime = 0
        self.addEvent("Lx", 100)
        self.addEvent("Lo", 130)
        self.addEvent("Lx", 500)
        self.addEvent("Lo", 530)
        self.addEvent("Lx", 800)
        self.addEvent("Lo", 830)
        self.addEvent("Ix", 200)
        self.addEvent("Io", 650)
        self.addEvent("Ix", 1200)
        self.addEvent("Io", 2650)
        self.addEvent("Tx", 200)
        self.addEvent("To", 220)
        self.addEvent("Tx", 1200)
        self.addEvent("To", 1220)
        self.addEvent("Tx", 1240)
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

class IntCurve:
    def __init__(self, name, index, color, yMax, pw):
        self.name = name
        self.yMin = index * 1.1
        
        self.x = [0]
        self.xBase = [0]
        self.y = [self.yMin]
        self.yBase = [self.yMin]
        self.yMax = yMax
        
        self.yPrev = 0
        self.xPrev = 0
        
        #init curve on plotwidget 'pw'
        self.sig = pw.plot(pen=color, name=self.name)
        self.sig.setData(self.x, self.y)
        self.base = pw.plot(pen=color)
        self.base.setData(self.xBase,self.yBase)
        fill = pg.FillBetweenItem(self.base, self.sig, color)
        pw.addItem(fill)
        
    
    def appendPoint(self, x, y):
        
        #add point to curve
        self.x.append(x)
        self.y.append(self.yPrev/self.yMax + self.yMin)
        self.x.append(x)
        self.y.append(y/self.yMax + self.yMin)
        
        #update base curve
        self.xBase.append(x)
        self.yBase.append(self.yMin)
        
        self.xPrev = x
        self.yPrev = y
        
        #update plot curve
        self.sig.setData(self.x, self.y)
        self.base.setData(self.xBase,self.yBase)
        

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

class GraphPerformance(QWidget):
    def __init__(self):
        self.app = QtGui.QApplication([])
        self.mw = QtGui.QMainWindow()
        self.mw.resize(800,500)
        self.mw.setWindowTitle('pyqtgraph example: PlotWidget')
        self.cw = QtGui.QWidget()
        self.mw.setCentralWidget(self.cw)
        self.l = QtGui.QVBoxLayout()
        self.cw.setLayout(self.l)    
        self.mw.show()

        self.pw = pg.PlotWidget(name='Plot1')
        self.l.addWidget(self.pw)
        
    def plotSession(self, trials, color):
        numToAverage = 50
        resultsBuffer = [False] * numToAverage
        numResults = 0
        points = []
        times = []
        for t in trials:
            wasSuccess = False
            if t.result == Results.CORRECT_REJECT or t.result == Results.HIT:
                wasSuccess = True
        
            resultsBuffer[numResults % numToAverage] = wasSuccess
            
            #actually do time between trials instead
            '''            
            if numResults > 0:
                resultsBuffer[numResults % numToAverage] = (trials[numResults].stateTimes[0] - trials[numResults-1].stateTimes[0])
            else:
                resultsBuffer[numResults % numToAverage] = 0
            '''             
            if numResults > len(resultsBuffer):
                percentCorrect = reduce((lambda x,y: int(x)+int(y)), resultsBuffer) / len(resultsBuffer) * 100
                points.append(percentCorrect)
                times.append((t.stateTimes[0] - trials[0].stateTimes[0])/1000)
            numResults += 1
             
        self.pw.plot(times,points,pen=pg.mkPen(color))
        self.pw.setXRange(min(times), max(times))
        self.pw.setYRange(0, 100)        
        
        
    def show(self):
        import sys
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

        
if __name__ == '__main__':
    gp = GraphPerformance()
    
    for x in range(0,10):
        trials = []
        tNum = 0
        for i in range(0,200):
            t = Trial()
            t.result = random.choice([Results.CORRECT_REJECT, Results.HIT, Results.ABORT, Results.TASK_FAIL])
            t.stateTimes.append(tNum)
            tNum += 1
            trials.append(t)
        
        gp.plotSession(trials,[x*25,255-x*25,random.randint(0,255)])
    
    gp.show()
    
