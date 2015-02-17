from __future__ import division
import math, random

def dPrime(sPlusHitRate, falseAlarmRate):
    zHit = invNormApprox(sPlusHitRate);
    zFA = invNormApprox(falseAlarmRate);
    dPrime = zHit - zFA;
    
    return dPrime

def criterion(sPlusHitRate, falseAlarmRate):
    zHit = invNormApprox(sPlusHitRate);
    zFA = invNormApprox(falseAlarmRate);
    c = -(zHit + zFA)/2;
    return c

def invNormApprox(p):
    #InvNormApprox:  Pass the hit rate and false alarm rate, and this
    #routine returns zHit and zFa.  d' = zHit - zFa.
    #Converted from a basic routine provided by:
    #Brophy, A. L. (1986).  Alternatives to a table of criterion 
    #  values in signal detection theory.  Behavior Research 
    #  Methods, Instruments, & Computers, 18, 285-286.
    #
    #Code adapted from http://memory.psych.mun.ca/models/dprime/
    #And just to be thorough, the results were confirmed against three other independent d' measurements.

    sign = -1
    
    if p > 0.5:
        p = 1-p
        sign = 1
    
    if p < 0.00001:
        z = 4.3;
        return round(z*sign,3)
    
    r = math.sqrt(-math.log(p))
    
    z = (((2.321213*r+4.850141)*r-2.297965)*r-2.787189)/((1.637068*r+3.543889)*r+1)
    return round(z*sign,3)


if __name__ == '__main__':
    testSet = ((0.5, 0.5), (0.0, 1.0), (1.0, 1.0), (0.75, 0.3), (0.9, 0.3), (0.68, 0.09))
    
    print "\nTesting dPrime(hitRate, falseAlarmRate)\n"
    for test in testSet:
        print "dPrime(" + str(test[0]) + ", " + str(test[1]) + "): " + str(dPrime(test[0], test[1]))
    
    