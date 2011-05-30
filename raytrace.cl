/* Size of the texture currently hard-coded */
#define SCREEN_H 512
#define SCREEN_W 512

/* With the current algorithm, this is the maximum number of voxels to
   traverse */
#define LOOP_LIMIT 200

/* Colors for the various sides of wall blocks */
#define WALL_UNDER ((float4)(0.3,0.5,0.5,1.0))
#define WALL_SIDE  ((float4)(0.45,0.75,0.75,1.0))
#define WALL_TOP   ((float4)(0.6,1.0,1.0,1.0))
#define WALLG_UNDER ((float4)(0.3,0.5,0.4,1.0))
#define WALLG_SIDE  ((float4)(0.45,0.75,0.45,1.0))
#define WALLG_TOP   ((float4)(0.6,1.0,0.6,1.0))

/* Edge types - what appears at the end of the grid */
#define ET_WALL         0
#define ET_PORTAL_TORUS 1
#define ET_SOLID_AIR    2

/* Block types */
#define BK_AIR      0
#define BK_WALL     1
#define BK_WALLG    2

/* Handy macro to get the element at a given location from the map
   grid */
#define GRID_GET(grid,x,y,z) ((grid)[x + y*x_size + z*x_size*y_size])
#define GRID_GETV(grid,v) GRID_GET((grid), (v).x,(v).y,(v).z)

__kernel void raytrace(__write_only __global image2d_t bmp,
    uchar x_size, uchar y_size, uchar z_size, uchar edge_type,
    float rot_x, float rot_y, float cam_x, float cam_y, float cam_z,
    float fov_x, float fov_y, __constant uchar *grid)
{
    /* Screen pixel position: */
    int2 p_pos = (int2)(get_global_id(0), get_global_id(1));

    /* Grid dimensions */
    uchar4 bounds = (uchar4)(x_size, y_size, z_size, 0);

    float4 ray_rot = (float4)(rot_x, rot_y,
                              (p_pos.x * fov_x) / SCREEN_W - fov_x/2,
                              (p_pos.y * fov_y) / SCREEN_H - fov_y/2);
    float4 rot_sin = sin(ray_rot),
           rot_cos = cos(ray_rot);

    /* Voxel traversal ray-tracing algorithm based on John Amanatides'
       and Andrew Woo's paper. */
    
    /* n is the vector of the ray as if the camera was looking directly
       down the z-axis without any rotation around it. */
    float4 n = (float4)(rot_cos.w * rot_sin.z,
                        -rot_sin.w,
                        rot_cos.w * rot_cos.z,
                        0.0f);
    
    // v is the unit vector along the ray in actual world coords
    float4 v = (float4)(
      n.x*rot_cos.x + n.y*rot_sin.x*rot_sin.y + n.z*rot_sin.x*rot_cos.y,
      n.y*rot_cos.y - n.z*rot_sin.y,
      -n.x*rot_sin.x + n.y*rot_cos.x*rot_sin.y + n.z*rot_cos.x*rot_cos.y,
      0.0f);

    /* u is the starting point of the ray */
    float4 u = (float4)(cam_x, cam_y, cam_z, 0.0f);
    // Thus equation of the ray = u + vt

    // P = (X,Y,Z) = current voxel coordinates
    int4 P = (int4)((int)u.x, (int)u.y, (int)u.z, 0);
    // TODO handle P being outside bounds of grid

    /* step = (stepX, stepY, stepZ) = values are either 1, 0, or -1.
       Components are determined from the sign of the components of v */
    char4 step = (char4)((char)sign(v.x), (char)sign(v.y),
                         (char)sign(v.z), 0);

    /* tmax = (tmaxX, tmaxY, tmaxZ) = values of t at which ray next
       crosses a voxel boundary in the respective direction */
    float4 tmax = (float4)((P.x + step.x - u.x)/v.x,
                           (P.y + step.y - u.y)/v.y,
                           (P.z + step.z - u.z)/v.z,
                           0.0f);

    /* dt = (dtX, dtY, dtZ) = how far along ray (in units of t) we must
       move for x/y/z component of move to equal width of one voxel */
    float4 dt = (float4)(step.x / v.x,
                         step.y / v.y,
                         step.z / v.z,
                         0.0f);

    /* justOut vector - used for checking we remain within the bounds
       of the grid */
    int4 justOut = (int4)(step.x == -1 ? -1 : bounds.x,
                          step.y == -1 ? -1 : bounds.y,
                          step.z == -1 ? -1 : bounds.z,
                          0);


    float4 ray_color = (float4)(0.0f, 0.0f, 0.0f, 0.0f);
    bool outside = false;
    char lastStep = 'x';

    #define STEP(dim) do { \
                        P.dim += step.dim; \
                        lastStep = (#dim)[0]; \
                        if (P.dim == justOut.dim) { \
                            outside = true; \
                        } else \
                        tmax.dim += dt.dim; \
                      } while (0)

    for (uint iter_count = 0; iter_count < LOOP_LIMIT; iter_count++) {
        uchar block_type = BK_AIR;

        if (tmax.x < tmax.y) {
            if (tmax.x < tmax.z) {
                STEP(x);
            } else {
                STEP(z);
            }
        } else {
            if (tmax.y < tmax.z) {
                STEP(y);
            } else {
                STEP(z);
            }
        }

        if (outside) {
            if (edge_type == ET_WALL) {
                block_type = BK_WALL;
            } /* else leave block_type as BK_AIR */
            // TODO ET_PORTAL_TORUS
        } else {
            block_type = GRID_GETV(grid, P);
        }

        if (block_type == BK_WALL) {
            if (lastStep != 'y') {
                // viewing block from side
                ray_color = WALL_SIDE;
            } else if (step.y == -1) {
                // viewing block from above
                ray_color = WALL_TOP;
            } else {
                // viewing block from below
                ray_color = WALL_UNDER;
            }
        } else if (block_type == BK_WALLG) {
            if (lastStep != 'y')
                ray_color = WALLG_SIDE;
            else if (step.y == -1)
                ray_color = WALLG_TOP;
            else
                ray_color = WALLG_UNDER;
        }

        if (outside || block_type != BK_AIR)
            break;

    }

    write_imagef(bmp, p_pos, ray_color);
}
