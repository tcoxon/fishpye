/* Size of the texture currently hard-coded */
#define SCREEN_W 640
#define SCREEN_H 480

/* With the current algorithm, this is the maximum number of voxels to
   traverse */
#define LOOP_LIMIT 100

/* Colors for the various sides of wall blocks */
#define COLOR_WALL  ((float4)(0.45,0.75,0.75,1.0))
#define COLOR_WALLG  ((float4)(0.45,0.75,0.45,1.0))

/* Multipliers for calculating shading on block faces */
#define LIGHTEN (4.0/3.0)
#define DARKEN (2.0/3.0)

/* Edge types - what appears at the end of the grid */
#define ET_WALL         0
#define ET_PORTAL_TORUS 1
#define ET_SOLID_AIR    2

/* Block types */
#define BK_AIR      0
#define BK_WALL     1
#define BK_WALLG    2
#define BK_PORTAL0  255

/* Handy macro for computing nearest axis boundary */
#define POSITIVE(X) ((X) > 0 ? (X) : 0)

/* Offset of grid within mapdat */
#define GRID_OFF 4

typedef struct world_t {
    uchar4 bounds;
    uint edge_type;
    __constant uchar *grid;
    __constant float *portals;
} world_t;

typedef struct ray_t {
    int4 P;
    float4 ray_color;
    uint outside;
    char4 last_step;
} ray_t;

/* `shading' values > 1.0 brighten, < 1.0 darken. */
float4 color_mix_shade(float4 color, float shading) {
    return (float4)(fmin(color.x * shading, 1.0f),
                    fmin(color.y * shading, 1.0f),
                    fmin(color.z * shading, 1.0f),
                    color.w);
}

float dot_prod(float4 i, float4 j) {
    return i.x * j.x + i.y * j.y + i.z * j.z + i.w * j.w;
}

float4 apply_matrix(float16 m_, float4 v) {
    union {
        float16 f;
        float m[16];
    } mu;
    mu.f = m_;
    float *m = mu.m;
    #define ELE(i) (m[i]*v.x + m[i+1]*v.y + m[i+2]*v.z + m[i+3]*v.w)
    return (float4)(ELE(0), ELE(4), ELE(8), ELE(12));
    #undef ELE
}

uchar grid_get(world_t w, int4 P) {
    return w.grid[P.x + (P.y * w.bounds.x) +
        (P.z * w.bounds.x * w.bounds.y)];
}

float16 get_portal(world_t w, uchar i) {
    __constant float *p = &w.portals[i*16];
    float16 result = (float16)(
        p[0], p[1], p[2], p[3],
        p[4], p[5], p[6], p[7],
        p[8], p[9], p[10], p[11],
        p[12], p[13], p[14], p[15]);
    return result;
}

/* Returns new ray_color. Halts ray if alpha is 1.0f.
   v is the unit vector of the ray; t is how far down the ray we are. */
float4 color_ray(world_t w, ray_t r, float4 v, float t)
{
    uchar block_type = BK_AIR;

    if (r.outside) {
        if (w.edge_type == ET_WALL) {
            block_type = BK_WALL;
        } else {
            /* else leave block_type as BK_AIR */
            // TODO ET_PORTAL_TORUS
            return (float4)(0.0f, 0.0f, 0.0f, 1.0f);
        }
    } else {
        block_type = grid_get(w, r.P);
    }

    float4 new_ray_color = r.ray_color;

    if (block_type != BK_AIR) {
        bool set_color = false;

        switch (block_type) {
        case BK_WALL:
            new_ray_color = COLOR_WALL;
            set_color = true;
            break;
        case BK_WALLG:
            new_ray_color = COLOR_WALLG;
            set_color = true;
            break;
        }

        if (set_color) {
            /* Calculate ambient lighting on this face */
            if (r.last_step.y == -1) {
                // viewing block from above
                new_ray_color = color_mix_shade(new_ray_color, LIGHTEN);
            } else if (r.last_step.y == 1) {
                // viewing block from below
                new_ray_color = color_mix_shade(new_ray_color, DARKEN);
            }

            /* Calculate diffuse lighting, reusing camera's position
               as light source. */
            float4 normal = (float4)(-r.last_step.x,
                                   -r.last_step.y,
                                   -r.last_step.z,
                                   -r.last_step.w);
            float diffuse_light = dot_prod(normal, v);
            /* The dot-product gives us -1.0 for fully lit surfaces,
               and 0.0 or < 0.0 for orthogonal and far surfaces */
            if (diffuse_light < 0.0f)
                /* Some magic numbers to make things look nice.
                   Technically, it should be 1/t^2, but who cares about
                   realism? */
                diffuse_light = 0.5f - diffuse_light / (0.6f * t);
            else
                diffuse_light = 0.0f;
            new_ray_color = color_mix_shade(new_ray_color, diffuse_light);
        }
    }

    return new_ray_color;
}

__kernel void raytrace(__write_only __global image2d_t bmp,
    float rot_x, float rot_y, float cam_x, float cam_y, float cam_z,
    float fov_x, float fov_y, __constant uchar *mapdat)
{
    world_t w;
    w.bounds = (uchar4)(mapdat[0], mapdat[1], mapdat[2], 0); /* Grid dimensions */
    w.edge_type = mapdat[3];
    w.grid = &mapdat[GRID_OFF];
    w.portals = (__constant float *)&mapdat[GRID_OFF +
        w.bounds.x*w.bounds.y*w.bounds.z];

    /* Screen pixel position: */
    int2 p_pos = (int2)(get_global_id(0), get_global_id(1));


    float4 ray_rot = (float4)(rot_x, rot_y,
                              (p_pos.x * fov_x) / SCREEN_W - fov_x/2,
                              (p_pos.y * fov_y) / SCREEN_H - fov_y/2);
    float4 rot_sin = sin(ray_rot),
           rot_cos = cos(ray_rot);

    /* Voxel traversal ray-tracing algorithm based on John Amanatides'
       and Andrew Woo's paper. */
    
    /* n is the vector of the ray as if the camera was looking directly
       down the z-axis without any rotation around it.
       Multiply it by rotation matrices to get v (below) */
    float4 n = (float4)(rot_cos.w * rot_sin.z,
                        -rot_sin.w,
                        rot_cos.w * rot_cos.z,
                        0.0f);
    
    ray_t r;

    // v is the unit vector along the ray in actual world coords
    float4 v = (float4)(
      n.x*rot_cos.x + n.y*rot_sin.x*rot_sin.y + n.z*rot_sin.x*rot_cos.y,
      n.y*rot_cos.y - n.z*rot_sin.y,
      -n.x*rot_sin.x + n.y*rot_cos.x*rot_sin.y + n.z*rot_cos.x*rot_cos.y,
      0.0f);

    /* u is the starting point of the ray */
    float4 u = (float4)(cam_x, cam_y, cam_z, 1.0f);
    // Thus equation of the ray = u + vt

    float t = 0.0f;

    // P = (X,Y,Z) = current voxel coordinates
    r.P = (int4)((int)u.x, (int)u.y, (int)u.z, 1);
    // TODO handle P being outside bounds of grid

    /* step = (stepX, stepY, stepZ) = values are either 1, 0, or -1.
       Components are determined from the sign of the components of v */
    char4 step;
    #define RESET_STEP do { \
        step = (char4)((char)sign(v.x), (char)sign(v.y), \
                       (char)sign(v.z), 0); \
    } while (0)
    RESET_STEP;

    /* tmax = (tmaxX, tmaxY, tmaxZ) = values of t at which ray next
       crosses a voxel boundary in the respective direction */
    float4 tmax;
    #define RESET_TMAX do { \
        tmax = (float4)((r.P.x + POSITIVE(step.x) - u.x)/v.x, \
                          (r.P.y + POSITIVE(step.y) - u.y)/v.y, \
                          (r.P.z + POSITIVE(step.z) - u.z)/v.z, \
                          0.0f); \
    } while (0)
    RESET_TMAX;

    /* dt = (dtX, dtY, dtZ) = how far along ray (in units of t) we must
       move for x/y/z component of move to equal width of one voxel */
    float4 dt;
    #define RESET_DT do { \
        dt = (float4)(step.x / v.x, step.y / v.y, step.z / v.z, 0.0f); \
    } while (0);
    RESET_DT;

    /* justOut vector - used for checking we remain within the bounds
       of the grid */
    int4 justOut;
    #define RESET_JUSTOUT do { \
        justOut = (int4)(step.x == -1 ? -1 : w.bounds.x, \
                         step.y == -1 ? -1 : w.bounds.y, \
                         step.z == -1 ? -1 : w.bounds.z, \
                         0); \
    } while (0)
    RESET_JUSTOUT;


    r.ray_color = (float4)(0.0f, 0.0f, 0.0f, 0.0f);
    r.outside = false;
    r.last_step = (char4)(0,0,0,0);

    // FIXME assuming camera is always inside the grid
    r.ray_color = color_ray(w, r, v, t);

    #define STEP(dim) do { \
                        r.P.dim += step.dim; \
                        r.last_step = (char4)(0,0,0,0); \
                        r.last_step.dim = step.dim; \
                        t = tmax.dim; \
                        if (r.P.dim == justOut.dim) { \
                            r.outside = true; \
                        } else \
                        tmax.dim += dt.dim; \
                      } while (0)

    for (uint iter_count = 0; iter_count < LOOP_LIMIT;
         iter_count++)
    {

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

        if (!r.outside && grid_get(w, r.P) == BK_PORTAL0) {
            float16 portal = get_portal(w, 0);

            u = apply_matrix(portal, u);
            v = apply_matrix(portal, v);
            r.P = (int4)((int)(u.x + v.x*t),
                         (int)(u.y + v.y*t),
                         (int)(u.z + v.z*t),
                         1);
            RESET_STEP;
            RESET_DT;
            RESET_TMAX;

            RESET_JUSTOUT;

        } else {
            r.ray_color = color_ray(w, r, v, t);
        }

        if (r.ray_color.w == 1.0f)
            break;

    }

    write_imagef(bmp, p_pos, r.ray_color);
}
