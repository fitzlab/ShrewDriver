import time, re
from SerialReader import SerialReader

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from events import *

comPortName = 'COM13'
portName = int(comPortName[3:])-1

class CurvePoints:
    def __init__(self, name, index, color, pw):
        self.name = name
        self.yMin = index * 1.1
        
        self.x = [self.yMin]
        self.xBase = [self.yMin]
        self.y = [self.yMin]
        self.yBase = [self.yMin]
        
        
        #init curve on plotwidget 'pw'
        self.sig = pw.plot(pen=color, name=self.name)
        self.sig.setData(self.x, self.y)
        self.base = pw.plot(pen=color)
        self.base.setData(self.xBase,self.yBase)
        fill = pg.FillBetweenItem(self.base, self.sig, color)
        pw.addItem(fill)
    
    def appendPoint(self, x, y):
        #add point
        if y==1:
            #low to high
            self.x.append(x)
            self.y.append(self.yMin)
            self.x.append(x)
            self.y.append(self.yMin+1)
        else:
            #high to low
            self.x.append(x)
            self.y.append(self.yMin+1)
            self.x.append(x)
            self.y.append(self.yMin)

        self.xBase.append(x)
        self.yBase.append(self.yMin)
        
        #update plot curve
        self.sig.setData(self.x, self.y)
        self.base.setData(self.xBase,self.yBase)
        
def msTimestampToString(msTimestamp):
    timeStr = ''
    hours = int(msTimestamp / (60*60*1000))
    if hours > 0:
        msTimestamp = msTimestamp - hours * (60*60*1000)
        timeStr += str(hours) + ":"
    
    minutes = int(msTimestamp / (60*1000))
    if minutes > 0 or hours > 0:
        msTimestamp = msTimestamp - minutes * (60*1000)
        timeStr += str(minutes).zfill(2) + ":"
    
    seconds = int(msTimestamp / (1000))
    if seconds > 0 or minutes > 0 or hours > 0:
        msTimestamp = msTimestamp - seconds * (1000)
        timeStr += str(seconds).zfill(2) + "."
    
    timeStr += str(int(msTimestamp)).zfill(3)
    
    return timeStr

class TimeAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        strns = []
        for x in values:
            strns.append(msTimestampToString(x))
        return strns

def checkSerial():
    #--- Poll serial and update plot ---#
    p = re.compile('\d+')
    lines = s.getUpdates()
    if not len(lines) == 0:
        for line in lines:
            #get timestamp
            t = 0
            if re.search('\d+', line):
                m = p.findall(line)
                t = long(m[0])
            
            #update the appropriate curve on the plot
            if re.search('So', line):
                stimPoints.appendPoint(t,0)
               
            if re.search('Sx', line):
                stimPoints.appendPoint(t,1)
           
            if re.search('Lo', line):
                lickPoints.appendPoint(t,0)
               
            if re.search('Lx', line):
                lickPoints.appendPoint(t,1)
           
            if re.search('Io', line):
                irPoints.appendPoint(t,0)
               
            if re.search('Ix', line):
                irPoints.appendPoint(t,1)
           
            if re.search('RH', line):
                highRewardPoints.appendPoint(t,1)
                highRewardPoints.appendPoint(t+1,0)
               
            if re.search('RL', line):
                lowRewardPoints.appendPoint(t,1)
                lowRewardPoints.appendPoint(t+1,0)
            
            #write line to disk
            print line

if __name__ == '__main__':
    #--- start reading serial port ---#
    s = SerialReader(portName)
    s.startReadThread()
    
    #--- init plot ---#
    axis = TimeAxis(orientation='bottom')
    app = pg.mkQApp()
    vb = pg.ViewBox()
    pw = pg.PlotWidget(viewBox=vb, axisItems={'bottom': axis}, enableMenu=False, title="")
    pw.showAxis('left', False)
    
    pw.setXRange(0, 10)
    pw.setYRange(0, 10)
    pw.show()
    pw.setWindowTitle('ShrewView Live')
    
    pw.addLegend()

    #prevent scaling+scrolling in Y, and don't go into negative x
    vb.setLimits(xMin=0, yMin=0, yMax=10, minYRange=10, maxYRange=10)
    vb.autoRange()
    
    #--- init plot curves ---#
    highRewardPoints = CurvePoints('High rewards', 4, [0,255,255], pw)
    lowRewardPoints = CurvePoints('Low rewards', 3, [0,255,0], pw)
    stimPoints = CurvePoints('reward available periods', 2, [128,128,128], pw)
    lickPoints = CurvePoints('licks', 1, [255,0,0], pw)
    irPoints = CurvePoints('IR', 0, [128,0,255], pw)
    
    #Start timer to check serial
    timer = QtCore.QTimer()
    timer.timeout.connect(checkSerial)
    timer.start(30)
    
    # Start Qt event loop unless running in interactive mode or using pyside.
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
