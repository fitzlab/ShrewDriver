import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import time
from events import *

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

class DateAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        strns = []
        rng = max(values)-min(values)
        timestr = ''
        if rng < 20*1000:
            string = '%H:%M:%S'
            label1 = '%b %d -'
            label2 = ' %b %d, %Y'
        else:
            string = '%Y'
            label1 = ''
            label2 = ''
        for x in values:
            strns.append(msTimestampToString(x))
        
        label = time.strftime(label1, time.localtime(min(values)))+time.strftime(label2, time.localtime(max(values)))
        return strns


if __name__ == '__main__':
    #pull in data
    filePath = "C:/python-projects/ShrewView/2014-09-08_sensorData.txt"
    events = readEvents(filePath)

    #custom plot init code
    axis = DateAxis(orientation='bottom')
    app = pg.mkQApp()
    vb = pg.ViewBox()
    pw = pg.PlotWidget(viewBox=vb, axisItems={'bottom': axis}, enableMenu=False, title="")
    pw.showAxis('left', False)
    
    pw.setXRange(-10, 10)
    pw.setYRange(0, 10)
    pw.show()
    pw.setWindowTitle('ShrewView')
    
    pw.addLegend()
    
    eventTypes = ['ir', 'lick', 'stim', 'lowReward', 'highReward']
    colors = [[128,0,255], [255,0,0], [128,128,128], [0,255,0], [0,255,255]]
    
    for k in range(len(eventTypes)-1,-1,-1):
        [x,y] = eventToCurve(events, eventTypes[k])
        y=y+k*1.1
        x0 = x
        y0 = np.zeros(len(y)) + k*1.1
        sig = pw.plot(pen=colors[k], name=eventTypes[k])
        sig.setData(x, y)
        base = pw.plot(pen=colors[k])
        base.setData(x0,y0)
        fill = pg.FillBetweenItem(base, sig, colors[k])
        pw.addItem(fill)
    
    #prevent scaling+scrolling in Y, and don't go into negative x
    vb.setLimits(xMin=0, yMin=0, yMax=10, minYRange=10, maxYRange=10)
    
    vb.autoRange()
    
    ## Start Qt event loop unless running in interactive mode or using pyside.
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    