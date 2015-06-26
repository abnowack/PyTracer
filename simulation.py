# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 11:50:01 2015

@author: Aaron

TODO: Implement Geometry Checking
    - Test if any lixels overlap
    - Cannot have hole in a hole, or solid in a solid
TODO: Use Bounded Volume Heirarchy to Reduce Lixel Search
TODO: Account for air attenuation by including outer material
      Currently will break if need to account for two materials in contact
"""
from mesh import angle_matrix
from geometry import Geometry, line_segment_intersect
from material import Material
from detector import DetectorArc, DetectorPlane
import numpy as np
import matplotlib.pyplot as plt

class Simulation(object):
    def __init__(self, universe_material, diameter=100., detector_width=100., detector='plane'):
        self.universe_material = universe_material
        self.geometry = Geometry()
        self.source = np.array([-diameter/2., 0.])
        if detector == 'plane':
            self.detector = DetectorPlane([diameter/2., 0.], detector_width)
        elif detector == 'arc':
            self.detector = DetectorArc([diameter/2., 0], diameter, detector_width/2., -detector_width/2.)
    
    def attenuation_length(self, start, end):
        atten_length = 0.        
        for i, lixel in enumerate(self.geometry.mesh.lixels):
            intercept = line_segment_intersect(self.geometry.mesh.points[lixel], np.array([start, end]))
            if intercept is not None:
                distance = np.sqrt((start[0] - intercept[0])**2. + (start[1] - intercept[1])**2.)
                normal = self.geometry.mesh.lixel_normal(i)
                sign = np.sign(np.dot(start - intercept, normal))
                inner_material = self.geometry.materials[self.geometry.inner_material_index[i]]
                outer_material = self.geometry.materials[self.geometry.outer_material_index[i]]
                atten_length += -sign * distance * inner_material.attenuation
        
        return atten_length
    
    def scan(self, angles=[0], nbins=100):
        atten_length = np.zeros((nbins, len(angles)))
        
        detector_bins = self.detector.create_bins(nbins)
        source = self.source
        
        for i, angle in enumerate(angles):
            rot = angle_matrix(angle)
            rot_source = np.inner(source, rot)
            rot_detector_bins = np.inner(detector_bins, rot)
            for j, detector_bin in enumerate(rot_detector_bins):
                atten_length[j, i] = self.attenuation_length(rot_source, detector_bin)
        
        return atten_length

    def draw(self):
        for solid in self.geometry.solids:
            lixels, points = solid.mesh.continuous_path_order()
            xs = [points[lixels[0, 0]][0]]
            ys = [points[lixels[0, 0]][1]]
            for lixel in lixels:
                if points[lixel[0]][0] == xs[-1] and points[lixel[0]][1] == ys[-1]:
                    xs.append(points[lixel[1]][0])
                    ys.append(points[lixel[1]][1])
                else:
                    xs.extend(points[lixel][:, 0])
                    ys.extend(points[lixel][:, 1])

            plt.fill(xs, ys, color=solid.color)
        
        if self.source is not None:
            plt.scatter(self.source[0], self.source[1], color='red', marker='x')
        
        detector_bins = self.detector.create_bins()
        plt.plot(detector_bins[:, 0], detector_bins[:, 1], color='green')

        plt.axis('equal')