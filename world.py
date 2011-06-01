
import math
import numpy 

import pyopencl as cl

# Edge types - i.e. what you see at the end of the grid (world/map)
ET_WALL = 0
ET_PORTAL_TORUS = 1
ET_SOLID_AIR = 2

# Block types - what may occupy a particular grid cell
BK_AIR = 0
BK_WALL = 1
BK_WALLG = 2

# Camera field-of-view modes
FOV_DEFAULT = math.pi/2
FOV_360 = 2*math.pi

# Speed of movement of the camera
WALK_SPEED = 4.0 # m/s

class world_object(object):
    def __init__(self, world):
        self.world = world
        (self.x, self.y, self.z) = (0.0,0.0,0.0)
        (self.rot_x, self.rot_y) = (0.0, 0.0) # No rot_z for now...
    def advance(self, t):
        pass
    def move_forward(self, dist, x, z):
        # dist can be -ve to move backward
        x = x + dist * math.sin(self.rot_x)
        z = z + dist * math.cos(self.rot_x)
        return (x,z)
    def move_sideways(self, dist, x, z):
        x = x - dist * math.cos(self.rot_x)
        z = z + dist * math.sin(self.rot_x)
        return (x,z)
    def move_up(self, dist, y):
        y = y + dist
        return y
    def try_move(self,x,y,z):
        moved = False
        # TODO what if the edge type is ET_PORTAL_TORUS
        if x != self.x and self.world.legal_x(x):
            self.x = x
            moved = True
        if z != self.z and self.world.legal_z(z):
            self.z = z
            moved = True
        if y != self.y and self.world.legal_y(y):
            self.y = y
            moved = True
        #if moved:
        #    print "pos = (%f, %f, %f)" % (self.x, self.y, self.z)

class physical_object(world_object):
    # TODO implement physics
    pass

class entity(physical_object):
    pass

class camera(world_object):
    def __init__(self, world):
        world_object.__init__(self, world)
        self.fov = FOV_DEFAULT
        # For transitions:
        self.prev_fov = self.fov
        self.target_fov = self.fov
        self.fov_trans_count = 0
    def advance(self, t):
        # Advance FOV transition:
        if self.fov != self.target_fov:
            self.fov_trans_count += t
        if self.fov_trans_count >= 1000:
            # takes 1000ms to complete transition
            self.fov = self.target_fov
            self.prev_fov = self.fov
            self.fov_trans_count = 0
        else:
            self.fov = (self.prev_fov + self.fov_trans_count *
                (self.target_fov-self.prev_fov)/1000)
    def fov_x(self):
        return self.fov
    def fov_y(self):
        return self.fov if self.fov <= math.pi else math.pi
    def toggle_fov(self):
        # Toggles FOV only if there is no current transition!
        if self.fov == FOV_DEFAULT:
            self.target_fov = FOV_360
        elif self.fov == FOV_360:
            self.target_fov = FOV_DEFAULT
    

class player_character(entity, camera):
    def __init__(self, world, x, y, z):
        entity.__init__(self, world)
        camera.__init__(self, world)

        (self.x, self.y, self.z) = (x, y, z)

        self.keys_down = set()

    def advance(self, t):
        camera.advance(self, t)
        entity.advance(self, t)

        # Move the camera if relevant key is down:
        dist = WALK_SPEED * t / 1000.0
        (x,y,z) = (self.x, self.y, self.z)
        if 'w' in self.keys_down:
            (x,z) = self.move_forward(dist, x, z)
        if 's' in self.keys_down:
            (x,z) = self.move_forward(-dist, x, z)
        if 'a' in self.keys_down:
            (x,z) = self.move_sideways(dist, x, z)
        if 'd' in self.keys_down:
            (x,z) = self.move_sideways(-dist, x, z)
        if ' ' in self.keys_down:
            y = self.move_up(dist, y)
        if 'n' in self.keys_down:
            y = self.move_up(-dist, y)
        self.try_move(x,y,z)

    def on_key_up(self, key, _x, _y):
        self.keys_down.remove(key)

    def on_key_down(self, key, _x, _y):
        self.keys_down.add(key)

        if key == 'o':
            camera.toggle_fov(self)

    def on_click(self, button, state, x, y):
        pass

    def on_mouse_motion(self, x, y):
        #print "Motion: %d, %d" % (x, y)
        self.rot_y += math.pi * y / 1000
        self.rot_x += math.pi * x / 1000

        if self.rot_y < -math.pi/2:
            self.rot_y = -math.pi/2
        elif self.rot_y > math.pi/2:
            self.rot_y = math.pi/2

        #print "rot = (%f, %f)" % (self.rot_x, self.rot_y)

class world(object):

    def __init__(self):
        self.world_shape = (self.x_size, self.y_size, self.z_size) = \
            (32, 16, 31)

        # Create 3D matrix of bytes to use as the grid
        self.grid = numpy.zeros(shape=self.world_shape,
            dtype=numpy.uint8, order='F')
        self.setup_grid()

        # What to display at the end of the world
        self.edge_type = ET_WALL

        self.player = player_character(self, 0.5, 1.5, 0.5)
        self.camera = self.player
        self.entities = [self.player]

    def init_cldata(self, ctx):
        self.grid_clbuf = cl.Buffer(ctx,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            size=(self.x_size * self.y_size * self.z_size),
            hostbuf=self.grid)

    def setup_grid(self):
        # Create alternating column of air and green blocks
        for i in xrange(1, 16, 2):
            self.grid[5][i][5] = BK_WALLG

        ## Build a house in the x=32,z=0 corner
        # Wall facing +z
        for x in xrange(25,32):
            for y in xrange(0,5):
                # with a window:
                if x != 27 or y != 1:
                    self.grid[x][y][5] = BK_WALL
        # Ceiling
        for x in xrange(25,32):
            for z in xrange(0,5):
                self.grid[x][5][z] = BK_WALL
        # Front:
        for z in xrange(0,6):
            for y in xrange(0,5):
                # with a door:
                if z != 2 or y > 1:
                    self.grid[24][y][z] = BK_WALL

    def legal_x(self, x):
        return x >= 0.0 and x < self.x_size
    def legal_z(self, z):
        return z >= 0.0 and z < self.z_size
    def legal_y(self, y):
        return y >= 0.0 and y < self.y_size

    def advance(self, t):
        """ Advance the world t ms """
        for e in self.entities:
            e.advance(t)

    def send_key_down(self, key, x, y):
        self.player.on_key_down(key, x, y)

    def send_key_up(self, key, x, y):
        self.player.on_key_up(key, x, y)

    def send_click(self, button, state, x, y):
        self.player.on_click(button, state, x, y)

    def send_mouse_motion(self, x, y):
        self.player.on_mouse_motion(x, y)
