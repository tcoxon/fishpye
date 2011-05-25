#define WALL_UNDER ((float4)(0.3,0.5,0.5,1.0))
#define WALL_SIDE  ((float4)(0.45,0.75,0.75,1.0))
#define WALL_TOP   ((float4)(0.6,1.0,1.0,1.0))

#define ET_WALL         0
#define ET_PORTAL_TORUS 1
#define ET_SOLID_AIR    2

__kernel void raytrace(__write_only __global image2d_t bmp,
    uchar x_size, uchar y_size, uchar z_size, uchar edge_type,
    __constant uchar *grid)
{
    uint x = get_global_id(0),
         y = get_global_id(1);
    int2 coords = (int2)(x,y);

    if (x < x_size && y < y_size) {
        write_imagef(bmp, coords, WALL_TOP);
    } else {
        write_imagef(bmp, coords, WALL_SIDE);
    }
}
