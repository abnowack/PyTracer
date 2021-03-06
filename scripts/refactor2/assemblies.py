"""
Create all of the assemblies of objects here
"""
from math import pi, floor
import numpy as np
from PIL import Image, ImageDraw
from collections import namedtuple

Data = namedtuple('Data', ['extent', 'data'])

def cartesian_to_image(x, y, extent, nx, ny):
    i = floor((x - extent[0]) / (extent[1] - extent[0]) * nx)
    j = floor((y - extent[2]) / (extent[3] - extent[2]) * ny)
    return i, j


def shielded_true_images(supersample=4):
    extent = np.array([-12, 12, -8, 8], dtype=np.double)
    delta = 0.2
    nx = int((extent[1] - extent[0]) / delta)
    ny = int((extent[3] - extent[2]) / delta)

    u235 = 0.2
    steel = 0.15
    poly = 0.3

    origin = -9 + 3.8 + 0.3
    outer_radius = 3.8
    inner_radius = 2.8

    snx, sny = nx*supersample, ny*supersample

    # transmission
    trans_im = Image.new('F', (nx*supersample, ny*supersample), color=0)
    draw = ImageDraw.Draw(trans_im)
    draw.rectangle([cartesian_to_image(-10, -5, extent, snx, sny),
                    cartesian_to_image(10, 5, extent, snx, sny)], fill=steel)
    draw.rectangle([cartesian_to_image(-9, -4, extent, snx, sny),
                    cartesian_to_image(9, 4, extent, snx, sny)], fill=0)

    draw.ellipse([cartesian_to_image(origin - outer_radius, -outer_radius, extent, snx, sny),
                  cartesian_to_image(origin + outer_radius, outer_radius, extent, snx, sny)], fill=u235)
    draw.ellipse([cartesian_to_image(origin - inner_radius, -inner_radius, extent, snx, sny),
                  cartesian_to_image(origin + inner_radius, inner_radius, extent, snx, sny)], fill=0)

    draw.rectangle([cartesian_to_image(5, 3, extent, snx, sny),
                    cartesian_to_image(7, 1, extent, snx, sny)], fill=steel)
    draw.rectangle([cartesian_to_image(5, -3, extent, snx, sny),
                    cartesian_to_image(7, -1, extent, snx, sny)], fill=poly)
    del draw
    trans_im = trans_im.resize((nx, ny), Image.BILINEAR)
    trans_arr = np.array(trans_im, dtype=np.double)

    # fission
    fission_im = Image.new('F', (snx, sny), color=0)
    draw = ImageDraw.Draw(fission_im)

    draw.ellipse([cartesian_to_image(origin - outer_radius, -outer_radius, extent, snx, sny),
                  cartesian_to_image(origin + outer_radius, outer_radius, extent, snx, sny)], fill=0.1)
    draw.ellipse([cartesian_to_image(origin - inner_radius, -inner_radius, extent, snx, sny),
                  cartesian_to_image(origin + inner_radius, inner_radius, extent, snx, sny)], fill=0)
    del draw
    fission_im = fission_im.resize((nx, ny), Image.BILINEAR)
    fission_arr = np.array(fission_im, dtype=np.double)

    # p
    p_im = Image.new('F', (snx, sny), color=0)
    draw = ImageDraw.Draw(p_im)
    draw.ellipse([cartesian_to_image(origin - outer_radius, -outer_radius, extent, snx, sny),
                  cartesian_to_image(origin + outer_radius, outer_radius, extent, snx, sny)], fill=1.0)
    draw.ellipse([cartesian_to_image(origin - inner_radius, -inner_radius, extent, snx, sny),
                  cartesian_to_image(origin + inner_radius, inner_radius, extent, snx, sny)], fill=0)
    del draw
    p_im = p_im.resize((nx, ny), Image.BILINEAR)
    p_mask = np.array(p_im, dtype=np.double)

    xs = np.arange(extent[0], extent[1], delta) + delta / 0.5
    ys = np.arange(extent[2], extent[3], delta) + delta / 0.5
    xs -= origin + 0.1
    ys -= 0
    ring_center_radius = (outer_radius - inner_radius) / 2 + inner_radius
    xv, yv = np.meshgrid(xs, ys)
    radius = np.sqrt(xv**2 + yv[::-1]**2)
    p_arr = -0.5 * (radius - ring_center_radius)**2 + 0.3
    slope = -0.05 / (1.1*3.8)
    p_arr += slope * xv - 0.05

    p_arr[p_mask <= 0] = 0
    p_arr[p_arr <= 0] = 0

    # p_arr = np.array(p_im, dtype=np.double)

    return [Data(extent, trans_arr), Data(extent, fission_arr), Data(extent, p_arr)]


def ut_logo():
    extent = np.array([-12, 12, -8, 8], dtype=np.double)

    im = Image.open("ut-icon-mono.bmp")
    rot_im = im.transpose(Image.FLIP_TOP_BOTTOM)

    ut_image = np.array(rot_im, dtype=np.double)
    ut_image = 1.0 - ut_image
    ut_image *= 0.1

    return [Data(extent, ut_image), Data(extent, ut_image), Data(extent, ut_image)]