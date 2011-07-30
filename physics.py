import numpy as np
import world
from math import *

def sign(x):
    return cmp(x, 0)

def positive(x):
    return x if x > 0 else 0

def trace_from_to(f, start, end):
    """
    f(x,y,z) -> Bool
    """
    last = (floor(end[0]), floor(end[1]), floor(end[2]))
    trace(
        lambda x, y, z: f(x,y,z) and (
            x != last[0] or y != last[1] or z != last[2]),
        start,
        (end[0] - start[0], end[1] - start[1], end[2] - start[2]))

TRACE_LOOP_LIMIT = 100
INF = float('inf')

def trace(f, u, v):
    """
    f(x,y,z) -> Bool
    u is the starting point of the ray in float coords
    v is the unit vector along the ray

    Uses J Amanatides and A Woo's voxel traversal algorithm to trace
    all the voxels from the starting point, u, along vector v until
    function f() returns False.
    """
    u = np.array([u[0], u[1], u[2], 1.0])
    v = np.array([v[0], v[1], v[2], 0.0])
    t = 0.0

    # p is the coordinate of the current voxel
    p = np.array([floor(u[0]), floor(u[1]), floor(u[2]), 1])

    # step components are -1, 0, or 1. Values determined from v
    step = np.array([sign(v[0]), sign(v[1]), sign(v[2]), 0])

    # tmax = values of t at which ray next crosses a voxel boundary
    tmax = np.array([
        (p[0] + positive(step[0]) - u[0]) / v[0] if step[0] != 0 else INF,
        (p[1] + positive(step[1]) - u[1]) / v[1] if step[1] != 0 else INF,
        (p[2] + positive(step[2]) - u[2]) / v[2] if step[2] != 0 else INF,
        0.0])

    # dt = how far along ray (in units of t) we must move for x/y/z
    # component of move to equal width of one voxel
    dt = np.array([
        step[0] / v[0] if step[0] != 0 else INF,
        step[1] / v[1] if step[1] != 0 else INF,
        step[2] / v[2] if step[2] != 0 else INF,
        0.0])

    for i in xrange(TRACE_LOOP_LIMIT):
        if not f(p[0], p[1], p[2]):
            break

        if tmax[0] < tmax[1]:
            if tmax[0] < tmax[2]:
                p[0] += step[0]
                t = tmax[0]
                tmax[0] += dt[0]
            else:
                p[2] += step[2]
                t = tmax[2]
                tmax[2] += dt[2]
        else:
            if tmax[1] < tmax[2]:
                p[1] += step[1]
                t = tmax[1]
                tmax[1] += dt[1]
            else:
                p[2] += step[2]
                t = tmax[2]
                tmax[2] += dt[2]
        # FIXME: portals

def blocking(w, x, y, z):
    return x < 0 or x >= w.x_size() or y < 0 or y >= w.y_size() or \
      z < 0 or z >= w.z_size() or world.blocking(w.grid_get(x,y,z))

def climb_step(w, obj, x, y, z, bx, by, bz):
    if obj.uy[0] == 0 and obj.uy[2] == 0:
        d = y-by
        if sign(obj.uy[1]) == 1:
            by = floor(by) + 1.0
        else:
            by = floor(by) - 0.005
        y = by + d
    elif obj.uy[0] == 0 and obj.uy[1] == 0:
        d = z-bz
        if sign(obj.uy[2]) == 1:
            bz = floor(bz) + 1.0
        else:
            bz = floor(bz) - 0.005
        z = bz + d
    elif obj.uy[1] == 0 and obj.uy[2] == 0:
        d = x-bx
        if sign(obj.uy[0]) == 1:
            bx = floor(bx) + 1.0
        else:
            bx = floor(bx) - 0.005
        x = bx + d
    else:
        # Don't climb any steps at weird angles like these
        pass
    return (x,y,z,bx,by,bz)

def legal_move(w, obj, x, y, z):
    """ legal_move: return the next position of an attempted move
    of obj from its current position to x,y,z """

    # Check the center of the object, after the move, is still within
    # the bounds of the grid. If it is not, and the object is a camera,
    # this could cause the renderer to crash
    reverted_all = True
    if x < 0.0 or x >= w.x_size():
        x = obj.x
    else:
        reverted_all = False
    if y < 0.0 or y >= w.y_size():
        y = obj.y
    else:
        reverted_all = False
    if z < 0.0 or z >= w.z_size():
        z = obj.z
    else:
        reverted_all = False

    if not reverted_all:
        # We didn't revert the coords to the original, so the desired
        # location is still within the bounds of the grid.

        # Where the foot (bottom) of the object would be if it moved to
        # the target location
        (bx,by,bz) = (x - obj.uy[0] * obj.hover_height,
                      y - obj.uy[1] * obj.hover_height,
                      z - obj.uy[2] * obj.hover_height)
        # If the target location is the step of a staircase, then the
        # following coordinates are within the block above the step
        (bxs,bys,bzs) = (x + sign(obj.uy[0]),
                         y + sign(obj.uy[1]),
                         z + sign(obj.uz[2]))
        if blocking(w, bx,by,bz) and not blocking(w, bxs,bys,bzs):
            (x, y, z, bx, by, bz) = \
              climb_step(w, obj, x, y, z, bx, by, bz)

        blocked = [False]
        def visit_cell(x,y,z):
            if blocking(w,x,y,z):
                blocked[0] = True
                return False
            return True
        # Visit every grid cell from the foot to the centre of the
        # object. If any are blocking cells, don't allow the move.
        # FIXME: trace_from_to won't work for portals
        trace_from_to(visit_cell, (bx,by,bz), (x,y,z))
        if blocked[0]:
            (x,y,z) = (obj.x, obj.y, obj.z)

    return (x,y,z)
