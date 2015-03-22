from __future__ import division
import fileinput, re, math, sys

from util.Stats import dPrime, criterion

sys.path.append("./trial")
from Trial import Trial

from Analyzer import Analyzer

sys.path.append("./global")
from Constants import *

if __name__ == '__main__':
    #do offline analysis
    taskErrorRates = []
    mLPerHours = []
    successRates = []
    sPlusResponseRates = []
    
    dirPath = "C:/Users/fitzlab1/Desktop/junk/"
    import glob
    import os
    os.chdir(dirPath)
    shrewName = 'other'
    if dirPath.lower().find("chico") > -1:
        shrewName= "Chico"
    for file in glob.glob("*.txt"):
        a = Analyzer(shrew=shrewName)
        filePath = dirPath + file
        
        a.readFile(filePath)
        
        msg = a.getSummaryResults()
        msg += a.getDiscriminationPerformance()
        msg += a.getTaskErrors()
        
        print msg
        
        print filePath + "\n\n\n\n\n"
