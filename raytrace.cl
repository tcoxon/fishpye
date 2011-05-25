#define SCREEN_H 512
#define SCREEN_W 512

#define MAX_DRAW_DIST 32

#define WALL_UNDER ((float4)(0.3,0.5,0.5,1.0))
#define WALL_SIDE  ((float4)(0.45,0.75,0.75,1.0))
#define WALL_TOP   ((float4)(0.6,1.0,1.0,1.0))

#define ET_WALL         0
#define ET_PORTAL_TORUS 1
#define ET_SOLID_AIR    2

#define BK_AIR      0
#define BK_WALL     1

#define INSIDE(pos, bounds) ((pos).x >= 0. && (pos).y >= 0. && \
    (pos).z >= 0. && (pos).x < (bounds).x && (pos).y < (bounds).y && \
    (pos).z < (bounds).z)

#define GRID_GET(grid,x,y,z) ((grid)[x + y*x_size + z*x_size*y_size])
#define GRID_GETV(grid,v) GRID_GET((grid), (v).x,(v).y,(v).z)

float ellip_radius_mix(float2 radii, float cos_theta) {
    float a = radii.x > radii.y ? radii.x : radii.y;
    float b = radii.x > radii.y ? radii.y : radii.x;

    float e2 = 1 - (b/a)*(b/a);
    return b / sqrt(1 - e2*cos_theta*cos_theta);
}

__kernel void raytrace(__write_only __global image2d_t bmp,
    uchar x_size, uchar y_size, uchar z_size, uchar edge_type,
    __constant uchar *grid)
{
    /* Screen pixel position: */
    int2 p_pos = (int2)(get_global_id(0), get_global_id(1));
    /* Camera position: */
    float4 c_pos = (float4)(0.5,0.5,0.5,0.0);
    float2 c_size = (float2)(1.,1.);
    uchar4 bounds = (uchar4)(x_size, y_size, z_size, 0);

    float2 ray_rot = (float2)((p_pos.x * M_PI_2) / SCREEN_W - M_PI_4,
                              (p_pos.y * M_PI_2) / SCREEN_H - M_PI_4);
    float2 ray_rot_sin = sin(ray_rot),
           ray_rot_cos = cos(ray_rot);

    float c_size_z = ellip_radius_mix(c_size, ray_rot_cos.y);
    float4 ray_pos = (float4)(
        c_pos.x + c_size.x*ray_rot_sin.x/2,
        c_pos.y + c_size.y*ray_rot_sin.y/2,
        c_pos.z + c_size_z*ray_rot_cos.x*ray_rot_cos.y/2, 0.);
    float4 ray_color = (float4)(0.,0.,0.,1.);
    uint steps = 0;
    while (steps < MAX_DRAW_DIST) {

        bool inside = INSIDE(ray_pos, bounds);
        uchar4 ray_posi = (uchar4)(ray_pos.x, ray_pos.y, ray_pos.z, ray_pos.w);

        uchar block;
        if (!inside) {
            block = edge_type == ET_WALL ? BK_WALL : BK_AIR;
        } else {
            block = GRID_GETV(grid, ray_posi);
        }

        if (block == BK_WALL) {
            /* Determine which face of the wall block we see, and set ray
               color accordingly. */
            // TODO
        }

        if (block != BK_AIR)
            break;

        // TODO: progress ray

        steps++;
    }

    write_imagef(bmp, p_pos, ray_color);
}
