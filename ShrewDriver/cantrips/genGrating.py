
from __future__ import division
from math import *
import numpy as np
from PIL import Image
import time

def getSquareWaveSample(position, period):
    position  = position % period;
    if position < period / 2:
        return 0
    else:
        return 1

def getSineWaveSample(position, period):
    position  = position % period;
    return sin(position / period * 2 * pi)


sizeX = 1280
sizeY = 1024

ori = 80 #in degrees
cosOri = cos(ori / 180 * pi)
sinOri = sin(ori / 180 * pi)

mat = np.float32(np.zeros(shape=(sizeY,sizeX)))
start_time = time.time()
for i in range(0,sizeY):
    for j in range(0,sizeX):
        mat[i][j] = getSquareWaveSample(j*cosOri + i*sinOri,300)
print("--- Took %s seconds ---"%(time.time() - start_time))
mat = mat*127.5 + 127.5
im2 = Image.fromarray(np.uint8(mat))
im2.show()
