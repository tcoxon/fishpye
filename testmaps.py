from world import *
import numpy

class testmap1(world):
    def setup_map(self):
        world.setup_map(self)

        ## Fill in grid

        # Create alternating column of air and green blocks
        for i in xrange(1, 16, 2):
            self.grid_set(5, i, 5, BK_WALLG)

        # Put a staircase on the z=0 wall
        for i in xrange(0,10):
            self.grid_set(i+5, i, 0, BK_WALL)

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
                    self.grid_set(23,y,z, BK_WALL)

        # Set up a demonstration portal into a reflected universe on floor:
        self.set_portal(0, numpy.matrix([
            [-1, 0, 0, 20],
            [0, 1, 0, 10],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]))
        for x in xrange(8, 12):
            for z in xrange(8, 12):
                self.grid_set(x, 0, z, BK_PORTAL[0])
        
        ## Set up a pair of linked portals:
        for x in xrange(20,22):
            for z in xrange(20,22):
                for y in xrange(0,3):
                    self.grid_set(x, y, z, BK_PORTAL[1])
        # Put pillars around this portal:
        for y in xrange(0, 3):
            for (x,z) in [(19,19),(19,22),(22,19),(22,22)]:
                self.grid_set(x, y, z, BK_WALL)
        # ... and a roof over it:
        for x in xrange(19,23):
            for z in xrange(19,23):
                self.grid_set(x, 3, z, BK_WALL)
        self.set_portal(1, numpy.matrix([
            [1, 0, 0, -10],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]))

        for x in xrange(10, 12):
            for z in xrange(20,22):
                for y in xrange(0,3):
                    self.grid_set(x, y, z, BK_PORTAL[2])
        # Put a wall behind this portal
        for z in xrange(19,23):
            for y in xrange(0,4):
                self.grid_set(9, y, z, BK_WALLG)
        self.set_portal(2, numpy.matrix([
            [1, 0, 0, 10],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]))
