__constant float min_re = -2.0,
            max_re = 1.0,
            min_im = -1.2,
            //max_im = min_im + (max_re-min_re) * height/width,
            max_im = 1.8,
            //re_factor = (max_re-min_re)/(width-1)
            re_factor = 0.005870841487279843,
            //im_factor = (max_im-min_im)/(width-1)
            im_factor = 0.005870841487279843;
__constant uint max_iter = 30;

__kernel void raycl(__write_only __global image2d_t bmp) {
    uint x = get_global_id(0),
         y = get_global_id(1);

    float c_im = max_im - y*im_factor,
          c_re = min_re + x*re_factor,
          z_re = c_re,
          z_im = c_im;

    bool is_inside = true;
    for (uint n = 0; n < max_iter; ++n) {
        float z_re2 = z_re*z_re,
              z_im2 = z_im*z_im;
        if (z_re2 + z_im2 > 4) {
            is_inside = false;
            break;
        }
        z_im = 2*z_re*z_im + c_im;
        z_re = z_re2 - z_im2 + c_re;
    }

    if (is_inside) {
        write_imagef(bmp, (int2)(x,y), (float4)(0.0,0.0,0.0,1.0));
    } else {
        write_imagef(bmp, (int2)(x,y), (float4)(1.0,1.0,1.0,1.0));
    }
}
