from __future__ import division
import time, re, sys, threading

import pyqtgraph as pg
from PyQt4.QtCore import * 
from PyQt4.QtGui import * 
from PyQt4 import QtCore
import numpy as np

class LivePlot(QWidget):
    
    #define signals that we will accept
    sigEvent = QtCore.pyqtSignal(str, float) 

    def __init__(self):
        self.startTime = time.time()
        
        
        #--- init plot ---#
        self.axis = TimeAxis(orientation='bottom')
        self.app = pg.mkQApp()
        self.vb = pg.ViewBox()
        self.pw = pg.PlotWidget(viewBox=self.vb, axisItems={'bottom': self.axis}, enableMenu=False, title="")
        self.pw.showAxis('left', False)
        
        self.pw.setXRange(0, 10)
        self.pw.setYRange(0, 10)
        self.pw.show()
        self.pw.setWindowTitle('ShrewView Live Plot')
        
        self.pw.addLegend()

        #prevent scaling+scrolling in Y, and don't go into negative x
        self.vb.setLimits(xMin=0, yMin=0, yMax=10, minYRange=10, maxYRange=10)
        self.vb.autoRange()
        
        #--- init plot curves ---#
        numStates = 7
        
        self.rewardPoints = IntCurve('Rewards', 4, [0,255,255], 1, self.pw)
        self.hintPoints = IntCurve('Hints', 3, [0,255,0], 1, self.pw)
        self.statePoints = IntCurve('State', 2, [128,128,128], numStates, self.pw)
        self.lickPoints = IntCurve('Licks', 1, [255,0,0], 1, self.pw)
        self.irPoints = IntCurve('IR', 0, [128,0,255], 1, self.pw)
        
        QWidget.__init__(self) 
        
        # Accept updates via signals. 
        # We have to do it via the Qt signals and slots system, because
        # we are using two threads, and Qt wants everything in one thread. 
        # So communication between threads must be done via signals, otherwise
        # things get weird (plot updates will be screwed up).
        self.sigEvent.connect(self.addEvent)
        
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
        if evtType.startswith('State'):
            stateNumber = int(evtType[5:])
            self.statePoints.appendPoint(t,stateNumber)
        if evtType == 'RL':
            self.hintPoints.appendPoint(t,1)
            self.hintPoints.appendPoint(t+0.001,0)
        if evtType == 'RH':
            self.rewardPoints.appendPoint(t,1)
            self.rewardPoints.appendPoint(t+0.001,0)
        
        super(LivePlot, self).repaint()
        super(LivePlot, self).setFocus()
        
    def addTestPoints(self):
        self.addEvent("Lx 100")
        self.addEvent("Lo 130")
        self.addEvent("Lx 500")
        self.addEvent("Lo 530")
        self.addEvent("Lx 800")
        self.addEvent("Lo 830")
        self.addEvent("Ix 200")
        self.addEvent("Io 650")
        self.addEvent("Ix 1200")
        self.addEvent("Io 2650")
        self.addEvent("State0 0")
        self.addEvent("State1 500")
        self.addEvent("State2 1000")
        self.addEvent("State3 1500")
        self.addEvent("State4 2000")
        self.addEvent("State5 2500")
        self.addEvent("State6 3000")
        self.addEvent("State7 3500")
        self.addEvent("State0 4000")
        self.addEvent("RL 650")
        self.addEvent("RL 1650")
        self.addEvent("RL 3650")
        self.addEvent("RH 700")
        self.addEvent("RH 2700")

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

if __name__ == '__main__':
    lp = LivePlot()
