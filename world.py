
import numpy 

import pyopencl as cl

ET_WALL = 0
ET_PORTAL_TORUS = 1
ET_SOLID_AIR = 2

class world(object):

    def __init__(self):
        self.world_shape = (self.x_size, self.y_size, self.z_size) = \
            (32, 16, 31)

        # Create 3D matrix of bytes to use as the grid
        self.grid = numpy.ndarray(shape=self.world_shape,
            dtype=numpy.uint8, order='F')

        # What to display at the end of the world
        self.edge_type = ET_WALL

    def init_cldata(self, ctx):
        self.grid_clbuf = cl.Buffer(ctx,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            size=(self.x_size * self.y_size * self.z_size),
            hostbuf=self.grid)
