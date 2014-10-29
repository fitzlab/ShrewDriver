from __future__ import division
import random

class Training():
    
    def __init__(self):
        self.sPlusOrientations = [0, 90]
        self.sMinusOrientations = [0]
        
        for i in range(0,10):
            self.chooseOrientations()
            print 'SMINUS: ' + str(self.sMinusOrientation)
            print 'SPLUS:  ' + str(self.sPlusOrientation)
            print '====='
    
    def chooseOrientations(self):
        # Randomly choose an S+ and an S- from the lists
        # Make sure they are different
        
        #Handle special case: If there's only one sMinus, make sure it's not in sPlus.
        if len(self.sMinusOrientations) == 1:
            if self.sMinusOrientations[0] in self.sPlusOrientations:
                idx = self.sPlusOrientations.index(self.sMinusOrientations[0])
                self.sPlusOrientations.pop(idx)
        
        #pick an sPlus, then pick an sMinus that's different from it.
        self.sPlusOrientation = random.choice(self.sPlusOrientations)
        if self.sPlusOrientation in self.sMinusOrientations:
            idx = self.sMinusOrientations.index(self.sPlusOrientation)
            poppedOri = self.sMinusOrientations.pop(idx)
            self.sMinusOrientation = random.choice(self.sMinusOrientations)
            self.sMinusOrientations.append(poppedOri)
        else:
            self.sMinusOrientation = random.choice(self.sMinusOrientations)

if __name__ == '__main__':
    x = Training()