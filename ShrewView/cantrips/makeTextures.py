import Image
import ImageDraw
import random
import math
import numpy as np
import re

#A collection of methods for making the textures we need for the 3D environment
class makeTextures:
    
    @staticmethod 
    def makeGratingTexture(width,height,pxGratingPeriod,orientation,contrast,gamma, offset, outFilePath):
      #We use a bigger image than necessary, since we're going to be rotating the bars to the
      #right orientation and then cropping to size.
      imSize = max(width,height)*2
      im = Image.new('L', (imSize,imSize))
      draw = ImageDraw.Draw(im)
      
      #Draw horizontal bars
      for h in range(0,imSize):
        if (h % pxGratingPeriod) >= math.ceil(pxGratingPeriod / 2):
          for w in range(0,imSize):
            intensity = math.pow(0.5+0.5*contrast,1/gamma)
            pxVal = 256*intensity
            im.putpixel((w,h),pxVal)
        else:
            for w in range(0,imSize):
                intensity = math.pow(0.5-0.5*contrast,1/gamma)
                pxVal = 256*intensity
                im.putpixel((w,h),pxVal)
            
      im = im.rotate(-orientation, Image.NEAREST, expand=1)
      imWidth, imHeight = im.size
      im = im.crop((int(imWidth/2-math.ceil(width/2.0)), 
        int(imHeight/2-math.ceil(height/2.0)), 
        int(imWidth/2+math.floor(width/2.0)), 
        int(imHeight/2+math.floor(height/2.0))))
      im.save(outFilePath)
   
    @staticmethod 
    def makeDotTexture(width,height,circleRadius,numCircles,outFilePath):
      im = Image.new('L', (width,height))
      draw = ImageDraw.Draw(im)
      #draw some circles!
      
      #We don't want circles colliding with each other, so we greedily add circles
      #to the most empty areas of the image. This requires maintaining a map of the 
      #distance from each pixel to its closest object (circles, or the border) as we add circles in.
    
      #initialize distance map with distance from each pixel to its nearest image border
      distMap = np.zeros((width,height))
      maxDist = 0
      maxDistW = 0
      maxDistH = 0
      for w in range(0,width,circleRadius/4):
        horDistToWall = w
        if w>width/2:
          horDistToWall = width-w
        for h in range(0,height,circleRadius/4):
          vertDistToWall = h
          if h>height/2:
            vertDistToWall = height-h
          if vertDistToWall > horDistToWall:
            distMap[w,h] = horDistToWall
          else:
            distMap[w,h] = vertDistToWall
          if distMap[w,h] > maxDist:
            maxDist = distMap[w,h]
            maxDistW = w
            maxDistH = h
        
      #add circles to empty areas of the image.
      #Each circle is perturbed by a small random amount (up to its radius) as it's added.
      #consistent random seed is a good thing here - we want the same texture every time
      random.seed(10) 
      for k in range(0,numCircles):
        print "Drawing circles (", str(k+1), "/", str(numCircles), ")"
        x = maxDistW + random.uniform(0, circleRadius/2)-circleRadius/4
        y = maxDistH + random.uniform(0, circleRadius/2)-circleRadius/4
        draw.ellipse((x-circleRadius, y-circleRadius, x+circleRadius, y+circleRadius),fill=(255))
        
        #update distance map
        maxDist = 0
        for w in range(0,width,circleRadius/4):
          dw2 = (x-w)*(x-w)
          for h in range(0,height,circleRadius/4):
            dh2 = (y-h)*(y-h)
            distToNew = math.sqrt(dw2+dh2)
            if distMap[w,h] > distToNew:
              #the new circle is closer to this point than anything else was
              distMap[w,h] = distToNew
            if distMap[w,h] > maxDist:
              maxDist = distMap[w,h]
              maxDistW = w
              maxDistH = h
              
      im.save(outFilePath)

if __name__ == '__main__':
    print 'making texture...'
    
    width = 2560
    height = 1600
    
    #width = 2560
    #height = 1600
    pxGratingPeriod = 240 #80 = high freq, 240 = low freq
    orientation = 90 
    contrast = 1.0
    gamma = 1.98 #The gamma of the target screen, usually 2.2ish
    outFilePath = './gratings/gray.png'
    makeTextures.makeGratingTexture(width,height,pxGratingPeriod,orientation,0,gamma, 0, outFilePath)
    
    print 'Making orientation textures'
    for contrast in np.arange(0.1,1.1,0.1):
        for orientation in np.arange(0,180,22.5):
            outFilePath = 'ori' + str(orientation) + 'period' + str(pxGratingPeriod) + 'contrast' + str(contrast)
            outFilePath = re.sub('\.', '_', outFilePath)
            outFilePath = './gratings/' + outFilePath +'.png'
            makeTextures.makeGratingTexture(width,height,pxGratingPeriod,orientation,contrast,gamma, 0, outFilePath)
            print 'wrote ' + outFilePath

    print 'done!'
