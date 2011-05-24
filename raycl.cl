
__kernel void raycl(__write_only __global image2d_t bmp) {

    int2 coords = (int2)(get_global_id(0), get_global_id(1));

    int width = get_image_width(bmp),
        height = get_image_height(bmp);

    float4 color = (float4)(1., 0., 0., 1.);

    if (coords.x == 50 && coords.y == 50) {
        color.x = color.y = 0.0;
        color.z = 1.0;
    } else {
        color.x = 1.0 * coords.x / width;
        color.y = 1.0 * coords.y / height;
    }

    write_imagef(bmp, coords, color);
}
