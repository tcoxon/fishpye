import sys
import numpy

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL import GLX
import pyopencl as cl

class raycl(object):
    def __init__(self, texture, tex_dim, world):
        self.tex_dim = tex_dim
        self.world = world

        self.clinit()
        self.loadProgram("raytrace.cl")

        world.init_cldata(self.ctx)

        self.tex = cl.GLTexture(
            self.ctx, cl.mem_flags.READ_WRITE,
            GL_TEXTURE_2D, 0,
            texture, 2)

        self.gl_objects = [self.tex]

    def clinit(self):
        plats = cl.get_platforms()
        ctx_props = cl.context_properties

        props = [(ctx_props.PLATFORM, plats[0]),
            (ctx_props.GL_CONTEXT_KHR, platform.GetCurrentContext())]

        import sys
        if sys.platform == "linux2":
            props.append((ctx_props.GLX_DISPLAY_KHR,
                GLX.glXGetCurrentDisplay()))
        elif sys.platform == "win32":
            props.append((ctx_props.WGL_HDC_KHR,
                WGL.wglGetCurrentDC()))
        
        self.ctx = cl.Context(properties=props)
        self.queue = cl.CommandQueue(self.ctx)

    def loadProgram(self, fname):
        f = open(fname, "r")
        code = "".join(f.readlines())
        self.program = cl.Program(self.ctx, code).build()

    def execute(self):
        glFinish()
        cl.enqueue_acquire_gl_objects(self.queue, self.gl_objects)

        global_size = self.tex_dim
        local_size = None
        world = self.world

        kernelargs = (self.tex,
                      numpy.uint8(world.x_size),
                      numpy.uint8(world.y_size),
                      numpy.uint8(world.z_size),
                      numpy.uint8(world.edge_type),
                      world.grid_clbuf)

        self.program.raytrace(self.queue, global_size, local_size,
            *kernelargs)

        cl.enqueue_release_gl_objects(self.queue, self.gl_objects)
        self.queue.flush()
        self.queue.finish()
