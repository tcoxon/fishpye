import numpy
import world

def legal_move(w, obj, x, y, z):
    """ legal_move: return the next position of an attempted move
    of obj from its current position to x,y,z """
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
        if world.blocking(w.grid_get(x,y,z)):
            (x,y,z) = (obj.x, obj.y, obj.z)
    return (x,y,z)
