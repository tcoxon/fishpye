
import math
import numpy 
import ctypes

import pyopencl as cl

# Edge types - i.e. what you see at the end of the grid (world/map)
ET_WALL = 0
ET_PORTAL_TORUS = 1
ET_SOLID_AIR = 2

# Block types - what may occupy a particular grid cell
BK_AIR = 0
BK_WALL = 1
BK_WALLG = 2
BK_PORTAL0 = 255

# Camera field-of-view modes
FOV_DEFAULT = math.pi/2
FOV_360 = 2*math.pi

# Speed of movement of the camera
WALK_SPEED = 4.0 # m/s
JUMP_VELOCITY = 6.0 # m/s

# Allocate 16kb for the map data. This is the most we can expect from most
# cards (though some go up to 64kb).
MAPDAT_SZ = 16*1024

# Offset of the grid within mapdat
GRID_OFF = 4

def blocking(block_type):
    return block_type != BK_AIR

def v(x,y,z):
    return numpy.array([x,y,z])

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
        (self.x,self.y,self.z) = self.world.legal_move(self,x,y,z)

class physical_object(world_object):
    def __init__(self, world, hover_height, radius):
        world_object.__init__(self, world)
        self.hover_height = hover_height
        self.radius = radius
        # Gravity belongs to the object. This way we can have crazy
        # physics fun with portals changing the direction of gravity
        self.gravity = v(0.0, -10.0, 0.0)
        self.vel = v(0.0,0.0,0.0)
        self.supported = False
    
    def physically_supported(self):
        return self.supported

    def advance(self, t):
        #world_object.advance(self, t)

        if self.world.physics_on:
            self.vel += self.gravity * t / 1000.0

            (nx,ny,nz) = (self.x, self.y, self.z)
            nx += self.vel[0] * t / 1000.0
            ny += self.vel[1] * t / 1000.0
            nz += self.vel[2] * t / 1000.0

            # FIXME Testing components for legality individually like this
            # only really works if velocity is quite low.
            self.y -= self.hover_height
            (self.x, self.y, self.z) = self.world.legal_move(self,
                nx, ny-self.hover_height, nz)
            self.y += self.hover_height

            if self.x != nx:
                self.vel[0] = 0.0
            if self.y != ny:
                self.vel[1] = 0.0
                self.supported = True
            else:
                self.supported = False
            if self.z != nz:
                self.vel[2] = 0.0

class entity(physical_object):
    def __init__(self, *args):
        physical_object.__init__(self, *args)
    def jump(self):
        self.vel[1] = JUMP_VELOCITY

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
        entity.__init__(self, world, 1.5, .40)
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
            if self.world.physics_on:
                if self.physically_supported():
                    self.jump()
            else:
                y = self.move_up(dist, y)
        if 'n' in self.keys_down:
            if not self.world.physics_on:
                y = self.move_up(-dist, y)
        self.try_move(x,y,z)

    def on_key_up(self, key, _x, _y):
        self.keys_down.remove(key)

        if key == 'p':
            self.world.physics_on = not self.world.physics_on

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
        self.setup_map()

        self.player = player_character(self, 0.5, 1.5, 0.5)
        self.camera = self.player
        self.entities = [self.player]

        self.physics_on = True

    def init_cldata(self, ctx):
        self.mapdat_clbuf = cl.Buffer(ctx,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            size=MAPDAT_SZ, hostbuf=self.mapdat)

    def x_size(self): return self.mapdat[0]
    def y_size(self): return self.mapdat[1]
    def z_size(self): return self.mapdat[2]
    def edge_type(self): return self.mapdat[3]
    def grid_get(self, x, y, z):
        return self.mapdat[GRID_OFF + int(x) +
            int(y) * self.x_size() +
            int(z) * self.x_size() * self.y_size()]
    def grid_set(self, x, y, z, v):
        self.mapdat[GRID_OFF + int(x) +
            int(y) * self.x_size() +
            int(z) * self.x_size() * self.y_size()] = v
    def get_portal_off(self):
        return GRID_OFF + self.x_size() * self.y_size() * self.z_size()
    def get_portal(self, i):
        flts = ctypes.cast(ctypes.byref(self.mapdat, self.get_portal_off() + 64*i),
            ctypes.POINTER(ctypes.c_float))
        return numpy.matrix([flts[0:4], flts[4:8], flts[8:12], flts[12:16]])
    def set_portal(self, i, portal):
        flts = ctypes.cast(ctypes.byref(self.mapdat, self.get_portal_off() + 64*i),
            ctypes.POINTER(ctypes.c_float))
        for x in xrange(0,4):
            for y in xrange(0,4):
                flts[x + y*4] = portal[x,y]

    def setup_map(self):
        # Create the array to use as the map data
        self.mapdat = (ctypes.c_byte*MAPDAT_SZ)(0)

        ## Set up mapdat header
        self.mapdat[0] = 31      # x_size
        self.mapdat[1] = 16      # y_size
        self.mapdat[2] = 31      # z_size
        self.mapdat[3] = ET_WALL # edge_type
        
        ## Fill in grid:
        # Create alternating column of air and green blocks
        for i in xrange(1, 16, 2):
            self.grid_set(5, i, 5, BK_WALLG)

        ## Build a house in the x=32,z=0 corner
        # Wall facing +z
        for x in xrange(24,31):
            for y in xrange(0,5):
                # with a window:
                if x != 26 or y != 1:
                    self.grid_set(x,y,5, BK_WALL)
        # Ceiling
        for x in xrange(24,31):
            for z in xrange(0,5):
                self.grid_set(x,5,z, BK_WALL)
        # Front:
        for z in xrange(0,6):
            for y in xrange(0,5):
                # with a door:
                if z != 2 or y > 1:
                    self.grid_set(24,y,z, BK_WALL)

        # Set up a demonstration portal:
        self.set_portal(0, numpy.matrix([
            [1, 0, 0, 0],
            [0, 1, 0, -10],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]))
        for x in xrange(8, 12):
            for z in xrange(8, 12):
                self.grid_set(x, 0, z, BK_PORTAL0)

    def legal_move(self, wo, x, y, z):
        """ legal_move: return the next position of an attempted move
        of wo (a world_object) from its current position to x,y,z """
        # changed_all really means reverted_all, as in all proposed
        # coordinates x,y,z have been reverted to the object's current
        # coordinates.
        changed_all = True
        if x < 0.0 or x >= self.x_size():
            x = wo.x
        else:
            changed_all = False
        if y < 0.0 or y >= self.y_size():
            y = wo.y
        else:
            changed_all = False
        if z < 0.0 or z >= self.z_size():
            z = wo.z
        else:
            changed_all = False
        if not changed_all:
            if blocking(self.grid_get(x,y,z)):
                (x,y,z) = (wo.x, wo.y, wo.z)
        return (x,y,z)

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
