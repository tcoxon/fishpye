
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys
import numpy
import ctypes

import raycl

class window(object):
    def __init__(self, *args, **kwargs):
        self.width = 640
        self.height = 480

        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
        glutInitWindowSize(self.width, self.height)
        self.win = glutCreateWindow("raycl")

        # gets called by GLUT every frame
        glutDisplayFunc(self.draw)

        # handle input
        glutKeyboardFunc(self.on_key)
        glutMouseFunc(self.on_click)
        glutMotionFunc(self.on_mouse_motion)

        # call draw every 30 ms
        glutTimerFunc(30, self.timer, 30)

        # seupt OpenGL scene
        self.glinit()

        self.texture = self.create_blank_texture()
        self.raycl = raycl.raycl(self.texture)

    def create_blank_texture(self):
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 512, 512, 0, GL_RGBA,
            GL_FLOAT, (ctypes.c_char_p("\x88" * (4*512*512))))
        return texture

    def glinit(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(-1, 1, 1, -1)
        glMatrixMode(GL_MODELVIEW)

    # Callbacks
    def timer(self, t):
        glutTimerFunc(t, self.timer, t)
        glutPostRedisplay()

    def on_key(self, *args):
        ESCAPE = '\033'
        if args[0] == ESCAPE or args[0] == 'q':
            sys.exit()

    def on_click(self, button, state, x, y):
        pass

    def on_mouse_motion(self, x, y):
        pass

    # draw stuff
    def draw(self):
        self.raycl.execute()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        self.draw_texture()
        #self.draw_axes()

        glutSwapBuffers()

    def draw_texture(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        glBegin(GL_QUADS)
        glTexCoord2d(0,0); glVertex2d(-1,-1)
        glTexCoord2d(1,0); glVertex2d(1,-1)
        glTexCoord2d(1,1); glVertex2d(1,1)
        glTexCoord2d(0,1); glVertex2d(-1,1)
        glEnd()

    def draw_axes(self):

        glBegin(GL_LINES)

        #X Axis
        glColor3f(1,0,0)    #red
        glVertex3f(0,0,0)
        glVertex3f(1,0,0)

        #Y Axis
        glColor3f(0,1,0)    #green
        glVertex3f(0,0,0)
        glVertex3f(0,1,0)

        #Z Axis
        glColor3f(0,0,1)    #blue
        glVertex3f(0,0,0)
        glVertex3f(0,0,1)

        #blah1
        glColor3f(0,0,1)    #blue
        glVertex3f(1,1,0)
        glVertex3f(0,1,0)
        glVertex3f(1,1,0)
        glVertex3f(1,0,0)

        glColor3f(1,1,1)
        glEnd()

if __name__ == "__main__":
    w = window()
    glutMainLoop()
