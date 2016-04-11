from __future__ import division
import sys
sys.path.append("..")


from numpy import *

def circleGaussianFade(rolloffStartPoint):
    #Makes an alpha mask with Gaussian rolloff
    maskSize = 512 #must be a power of 2. Higher gives nicer resolution but longer compute time.
    sigma = 0.12 #decays nicely to < 1% contrast at the edge
    twoSigmaSquared = 2*pow(sigma,2) #handy for later
    
    mask = ones([maskSize, maskSize])

    maskCenter = maskSize / 2
    rolloffStartPx = maskSize / 2 * rolloffStartPoint
    rolloffStartPxSquared = pow(rolloffStartPx, 2)
    rolloffLengthPx = (1-rolloffStartPoint)*maskSize/2

    #This is just distance formula calculated a bit faster
    squaredDistances = zeros(maskSize) 
    for i in xrange(0,maskSize):
        squaredDistances[i] = math.pow(i-maskCenter, 2)
    
    # Fill in alpha values to produce Gaussian rolloff.
    # Note: In PsychoPy, -1 is "nothing", 0 is "half contrast", 1 is "full contrast".
    for i in xrange(0,maskSize):
        for j in xrange(0,maskSize):
            dSquared = squaredDistances[i] + squaredDistances[j]
            if dSquared > rolloffStartPxSquared:
                #we are outside the main circle, so fade appropriately
                fadeProportion = (math.sqrt(dSquared)-rolloffStartPx) / rolloffLengthPx
                if fadeProportion > 1:
                    #we are outside the circle completely, so we want "nothing" here.
                    mask[i,j] = -1
                else:
                    x = fadeProportion / 2 #input to Gaussian function, in range [0,0.5]
                    alphaValue = math.exp(-pow(x,2)/twoSigmaSquared)*2 - 1
                    mask[i,j] = alphaValue
        
    return mask

def circleLinearFade(rolloffStartPoint):
    #Makes an alpha mask with linear rolloff
    maskSize = 512 #must be a power of 2. Higher gives nicer resolution but longer compute time.
    
    mask = ones([maskSize, maskSize])

    maskCenter = maskSize / 2
    rolloffStartPx = maskSize / 2 * rolloffStartPoint
    rolloffStartPxSquared = pow(rolloffStartPx, 2)
    rolloffLengthPx = (1-rolloffStartPoint)*maskSize/2

    #This is just distance formula calculated a bit faster
    squaredDistances = zeros(maskSize) 
    for i in xrange(0,maskSize):
        squaredDistances[i] = math.pow(i-maskCenter, 2)
    
    # Fill in alpha values to produce linear rolloff.
    # Note: In PsychoPy, -1 is "nothing", 0 is "half contrast", 1 is "full contrast".
    for i in xrange(0,maskSize):
        for j in xrange(0,maskSize):
            dSquared = squaredDistances[i] + squaredDistances[j]
            if dSquared > rolloffStartPxSquared:
                #we are outside the main circle, so fade appropriately
                fadeProportion = (math.sqrt(dSquared)-rolloffStartPx) / rolloffLengthPx
                if fadeProportion > 1:
                    #we are outside the circle completely, so we want "nothing" here.
                    mask[i,j] = -1
                else:
                    mask[i,j] = 1-fadeProportion*2
        
    return mask
