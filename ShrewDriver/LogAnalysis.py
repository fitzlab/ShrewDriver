from __future__ import division
import fileinput, re, math, sys, random

from util.Stats import dPrime, criterion

from GraphPerformance import GraphPerformance
from pyqtgraph.Qt import QtGui, QtCore

sys.path.append("./trial")
from Trial import Trial

#from AnalyzerRetry import Analyzer
from Analyzer import Analyzer

sys.path.append("./global")
from Constants import *

if __name__ == '__main__':
    #do offline analysis
    taskErrorRates = []
    mLPerHours = []
    successRates = []
    sPlusResponseRates = []
    
    dirPath = r"C:\Users\fitzlab1\Desktop\chico_0609" + "\\"
    import glob
    import os
    os.chdir(dirPath)
    shrewName = 'other'
    if dirPath.lower().find("chico") > -1:
        shrewName= "Chico"
        
    
    gp = GraphPerformance()
    
    for file in glob.glob("*.txt"):
        filePath = dirPath + file
        
        a = Analyzer(shrew=shrewName)     
        a.readFile(filePath)
        
           
        a.recomputeIfNeeded()        
        msg = a.getSummaryResults()
        msg += a.getDiscriminationPerformance()
        msg += a.getTaskErrors()
        msg += filePath + "\n\n\n\n\n"
           
        print msg
        
        
        #gp.plotSession(a.trials, [random.randint(0,255),random.randint(0,255),random.randint(0,255)])
        
        '''
        a.recomputeIfNeeded()
        sMinus = a.sMinusPerformances.keys()[0]
        nSMinusCorrect = a.sMinusPerformances[sMinus].numCorrect
        nSMinusTrials = a.sMinusPerformances[sMinus].numTrials
        percentCorrect = nSMinusCorrect / nSMinusTrials
        dPrime = a.sMinusPerformances[sMinus].dPrime
        
        sPlus = a.sPlusPerformances.keys()[0]
        nSPlusCorrect = a.sPlusPerformances[sPlus].numCorrect
        nSPlusTrials = a.sPlusPerformances[sPlus].numTrials
        percentSPlusCorrect = nSPlusCorrect / nSPlusTrials
        
        percentDiscrimCorrect = (nSMinusCorrect + nSPlusCorrect) / (nSMinusTrials + nSPlusTrials) * 100
        
        nTotalTrials = nSPlusTrials + nSMinusTrials
        
        
        msg = str(sMinus) + " " 
        #msg += "s+:" + str(nSPlusCorrect) + "/" 
        #msg += str(nSPlusTrials) + " " 
        #msg += "s-:" + str(nSMinusCorrect) + "/" 
        #msg += str(nSMinusTrials) + " " 
        #msg += str(round(percentCorrect,3)) + " "
        #msg += str(round(percentSPlusCorrect,3)) + " "
        #msg += str(dPrime) + " " 
        #msg += str(nTotalTrials) + " " 
        #msg += str(percentDiscrimCorrect) + " " 
        msg += str(a.taskErrorRate) + " " 
        print msg
        '''
    
    #gp.show()
        
        