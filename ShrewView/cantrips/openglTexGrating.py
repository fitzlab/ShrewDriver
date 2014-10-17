from __future__ import division
import pyglet
from pyglet.gl import *

winWidth = 800
winHeight = 800

win = pyglet.window.Window(width=winWidth, height=winHeight)
import numpy

from OpenGL.GL import *
from OpenGL.GLU import *

from ctypes import *
from math import *

#make image
texWidth=360
texImg = numpy.zeros([texWidth,1,1])
intensity = 0
for i in range(0, texWidth):
    texImg[i] = sin(i/10)
texImg = (texImg + 1) / 2

#bullshit
texture = glGenTextures(1)
glBindTexture( GL_TEXTURE_1D, texture );
glTexEnvf( GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE );
glTexParameterf( GL_TEXTURE_1D, GL_TEXTURE_WRAP_S,GL_REPEAT);
glTexParameterf( GL_TEXTURE_1D, GL_TEXTURE_WRAP_T,GL_REPEAT );
glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexImage1D(GL_TEXTURE_1D, 0, GL_LUMINANCE, texWidth, 0, GL_LUMINANCE, GL_FLOAT, texImg)
glEnable( GL_TEXTURE_1D );

patchWidth = int(600 * 2)
patchHeight = int(600 * 2)

patchOffsetX = -int((patchWidth-winWidth) / 2)
patchOffsetY = -int((patchWidth-winWidth) / 2)

@win.event
def on_draw():

    # Clear buffers
    glClear(GL_COLOR_BUFFER_BIT)
    
    glTranslatef(winWidth/2, winWidth/2, 0)
    glRotatef(1, 0, 0, 1)
    glTranslatef(-winWidth/2, -winWidth/2, 0)
    
    # Draw some stuff
    glTranslatef(patchOffsetX, patchOffsetY, 0)
    glBegin (GL_QUADS);
    glTexCoord2i (0, 0)
    glVertex2i (0, 0)
    glTexCoord2i (1, 0)
    glVertex2i (patchWidth, 0)
    glTexCoord2i (1, 1)
    glVertex2i (patchWidth, patchHeight)
    glTexCoord2i (0, 1)
    glVertex2i (0, patchHeight)
    glEnd()
    glTranslatef(-patchOffsetX, -patchOffsetY, 0)
 
pyglet.app.run()