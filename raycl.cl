__kernel void raycl(__write_only __global image2d_t bmp) {
    int2 coords = (get_global_id(0), get_global_id(1));
    write_imagef(bmp, coords, (1.0, 1.0, 1.0, 1.0));
}
