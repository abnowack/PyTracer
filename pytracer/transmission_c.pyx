# cython: profile=False
import numpy as np

cimport numpy as np
from cython cimport cdivision, boundscheck, wraparound
from libc.math cimport sqrt

cdef inline double distance(double x1, double y1, double x2, double y2):
    cdef:
        double tmp = 0

    tmp = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)
    return sqrt(tmp)

cdef inline double sign_line(double x, double y, double x1, double y1, double x2, double y2):
    return (x - x1) * (y1 - y2) + (y - y1) * (x2 - x1)

@cdivision(True)
cpdef point_segment_distance(double px, double py, double x0, double x1, double y0, double y1):
    cdef:
        double length_sq, t, projection_x, projection_y, distance

    length_sq = (x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0)
    if length_sq <= 0:
        distance = sqrt((px - x0) * (px - x0) + (py - y0) * (py - y0))
        return distance

    t = (px - x0) * (x1 - x0) + (py - y0) * (y1 - y0)
    t /= length_sq
    if t > 1:
        t = 1
    elif t < 0:
        t = 0

    projection_x = x0 + t * (x1 - x0)
    projection_y = y0 + t * (y1 - y0)
    distance = (px - projection_x) * (px - projection_x) + (py - projection_y) * (py - projection_y)
    distance = sqrt(distance)
    return distance


@cdivision(True)
@boundscheck(False)
cpdef absorbance_at_point(double point_x, double point_y, double[:, :, ::1] segments, double[:, ::1] absorbance):
    """ Based on looking at segment with smallest distance """
    cdef:
        double min_distance = 1e99
        double distance
        double is_outer
        double point_absorbance = 0

    for i in range(segments.shape[0]):
        distance = point_segment_distance(point_x, point_y, segments[i, 0, 0], segments[i, 1, 0],
                                          segments[i, 0, 1], segments[i, 1, 1])
        if distance < min_distance:
            min_distance = distance
            is_outer = sign_line(point_x, point_y, segments[i, 0, 0], segments[i, 0, 1],
                                 segments[i, 1, 0], segments[i, 1, 1])
            if is_outer == 0:
                point_absorbance = (absorbance[i, 1] + absorbance[i, 0]) / 2
            elif is_outer > 0:
                point_absorbance = absorbance[i, 1]
            else:
                point_absorbance = absorbance[i, 0]
    return point_absorbance


@cdivision(True)
# @boundscheck(False)
cpdef absorbance_image(double[:, ::1] image, double[::1] xs, double[::1] ys,
                       double[:, :, ::1] segments, double[:, ::1] absorbance):

    for i in range(xs.shape[0]):
        for j in range(ys.shape[0]):
            image[i, j] = absorbance_at_point(xs[i], ys[j], segments, absorbance)


# TODO Make this more safe if intersects or indexes isn't passed correctly
@cdivision(True)
@boundscheck(False)
cpdef int intersections(double[::1] start, double[::1] end, double[:, :, ::1] segments,
                        double[:, ::1] intersect_cache, int[::1] index_cache, bint ray):
    cdef:
        int i, num_intersect = 0
        double r[2]
        double s[2]
        double denom, t, u, epsilon = 1e-15

    for i in range(segments.shape[0]):
        r[0] = segments[i, 1, 0] - segments[i, 0, 0]
        r[1] = segments[i, 1, 1] - segments[i, 0, 1]
        s[0] = end[0] - start[0]
        s[1] = end[1] - start[1]

        denom = r[0] * s[1] - r[1] * s[0]
        if denom == 0.:
            continue

        t = (start[0] - segments[i, 0, 0]) * s[1] - (start[1] - segments[i, 0, 1]) * s[0]
        t = t / denom
        u = (start[0] - segments[i, 0, 0]) * r[1] - (start[1] - segments[i, 0, 1]) * r[0]
        u = u / denom

        if -epsilon < t < 1. - epsilon:
            if (ray) or 0. < u <= 1.:
                intersect_cache[num_intersect, 0] = segments[i, 0, 0] + t * r[0]
                intersect_cache[num_intersect, 1] = segments[i, 0, 1] + t * r[1]
                index_cache[num_intersect] = i
                num_intersect += 1

    return num_intersect

@cdivision(True)
@boundscheck(False)
@wraparound(False)
cpdef double absorbance(double[::1] start, double[::1] end,
                        double[:, :, ::1] segments, double[:, ::1] seg_absorption,
                        double universe_absorption, double[:, ::1] intersect_cache,
                        int[::1] index_cache):
    cdef:
        int num_intersect = 0
        double absorbance = 0
        double current_distance = 0, min_distance = 1e15
        double tmp, tmp2
        int i, ci

    num_intersect = intersections(start, end, segments, intersect_cache, index_cache, ray=False)

    # If no intersection must determine what material we are within by tracing a ray
    if num_intersect == 0:
        num_intersect = intersections(start, end, segments, intersect_cache, index_cache, ray=True)

    # No intersection through a ray, must be outside the object, return absorbance from universe material
    if num_intersect == 0:
        absorbance = distance(start[0], start[1], end[0], end[1]) * universe_absorption
        return absorbance

    for i in range(num_intersect):
        current_distance = distance(intersect_cache[i, 0], intersect_cache[i, 1], start[0], start[1])
        if current_distance < min_distance:
            ci = index_cache[i]
            min_distance = current_distance

    tmp = sign_line(start[0], start[1], segments[ci, 0, 0], segments[ci, 0, 1], segments[ci, 1, 0], segments[ci, 1, 1])

    if tmp > 0:
        absorbance = distance(start[0], start[1], end[0], end[1]) * seg_absorption[ci, 1]
    else:
        absorbance = distance(start[0], start[1], end[0], end[1]) * seg_absorption[ci, 0]

    # Had intersections, so add up all individual absorptions between start and end
    for i in range(num_intersect):
        ci = index_cache[i]
        tmp = sign_line(start[0], start[1], segments[ci, 0, 0], segments[ci, 0, 1], segments[ci, 1, 0], segments[ci, 1, 1])
        tmp2 = distance(intersect_cache[i, 0], intersect_cache[i, 1], end[0], end[1]) * (seg_absorption[ci, 0] - seg_absorption[ci, 1])
        if tmp > 0:
            absorbance += tmp2
        else:
            absorbance -= tmp2
    return absorbance

@boundscheck(False)
@wraparound(False)
cpdef void absorbances(double[:, ::1] start, double[:, ::1] end,
                       double[:, :, ::1] segments, double[:, ::1] seg_absorption,
                       double universe_absorption, double[:, ::1] intersects_cache,
                       int[::1] indexes_cache, double[:] absorbance_cache):
    cdef:
        int i

    for i in range(start.shape[0]):
        absorbance_cache[i] = absorbance(start[i], end[i], segments, seg_absorption, universe_absorption,
                                         intersects_cache, indexes_cache)
