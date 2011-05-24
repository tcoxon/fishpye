import sys
import numpy
import ctypes
import time

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import raycl

class window(object):
    def __init__(self, *args, **kwargs):
        self.width = 640
        self.height = 480

        self.tex_w = 512
        self.tex_h = 512

        self.count_to_30 = 0

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
        self.raycl = raycl.raycl(self.texture, self.tex_w, self.tex_h)

    def create_blank_texture(self):
        tex_buf = (ctypes.c_char_p(
            # initial value:
            "\x88" * (4*self.tex_w*self.tex_h)))

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8,
            self.tex_w, self.tex_h, 0, GL_RGBA,
            GL_FLOAT, tex_buf)

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
        if self.count_to_30 == 0:
            self.time_start = time.time()
            
        self.raycl.execute()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        self.draw_texture()
        #self.draw_axes()

        glutSwapBuffers()

        self.count_frame()

    def count_frame(self):
        self.count_to_30 += 1
        if self.count_to_30 >= 30:
            self.count_to_30 = 0
            
            dt = time.time() - self.time_start

            fps = 30 / dt

            print "%f fps" % fps

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
