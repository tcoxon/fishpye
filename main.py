import sys
import numpy
import ctypes
import time

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import raycl
import world

class window(object):
    def __init__(self, *args, **kwargs):
        self.width = 640
        self.height = 480
        self.cx = self.width / 2
        self.cy = self.height / 2

        self.tex_dim = (640,480)

        self.count_to_30 = 0

        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
        glutInitWindowSize(self.width, self.height)
        self.win = glutCreateWindow("raycl")

        # gets called by GLUT every frame
        glutDisplayFunc(self.draw)

        # handle input
        self.skip_first_motion = True
        glutEntryFunc(self.on_mouse_enter)
        glutIgnoreKeyRepeat(1)
        glutKeyboardFunc(self.on_key_down)
        glutKeyboardUpFunc(self.on_key_up)
        glutMouseFunc(self.on_click)
        glutPassiveMotionFunc(self.on_mouse_motion)

        # Limit to 50fps
        glutTimerFunc(20, self.timer, 20)

        # set up OpenGL scene
        self.glinit()

        # set up world for the game
        self.world = world.world()

        # set up display texture and opencl
        self.texture = self.create_blank_texture()
        self.raycl = raycl.raycl(self.texture, self.tex_dim,
            self.world)

    def create_blank_texture(self):
        tex_buf = (ctypes.c_char_p(
            # initial value:
            "\x88" * (4*self.tex_dim[0]*self.tex_dim[1])))

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8,
            self.tex_dim[0], self.tex_dim[1], 0, GL_RGBA,
            GL_FLOAT, tex_buf)

        return texture

    def glinit(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(-1, 1, 1, -1)
        glMatrixMode(GL_MODELVIEW)

    def reset_pointer(self):
        glutWarpPointer(self.cx, self.cy)

    # Callbacks
    def timer(self, t):
        glutTimerFunc(t, self.timer, t)
        self.world.advance(t)
        glutPostRedisplay()

    def on_key_down(self, key, x, y):
        ESCAPE = '\033'
        if key == ESCAPE or key == 'q':
            sys.exit()
        else:
            self.world.send_key_down(key, x, y)

    def on_key_up(self, key, x, y):
        self.world.send_key_up(key, x, y)

    def on_click(self, button, state, x, y):
        self.world.send_click(button, state, x, y)

    def on_mouse_motion(self, x, y):
        if x != self.cx and y != self.cy:
            if not self.skip_first_motion:
                self.world.send_mouse_motion(x - self.cx, y - self.cy)
            else:
                self.skip_first_motion = False
            self.reset_pointer()

    def on_mouse_enter(self, state):
        if state == GLUT_ENTERED:
            self.reset_pointer()
            glutSetCursor(GLUT_CURSOR_NONE)
            self.skip_first_motion = True

    # draw stuff
    def draw(self):
        if self.count_to_30 == 0:
            self.time_start = time.time()
            
        self.raycl.execute()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        self.draw_texture()
        if self.count_to_30 < 15:
            self.draw_axes()

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
