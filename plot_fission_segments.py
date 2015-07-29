from mesh import create_hollow, translate_rotate_mesh, create_rectangle, create_circle, angle_matrix
from material import Material
from solid import Solid
from simulation import Simulation

import numpy as np
import matplotlib.pyplot as plt
import sys

def plot_macro_fission(sim, start, end):
    start_points, end_points, macro_fissions = sim.fission_segments(start, end)
    print start_points
    print end_points
    for i in xrange(len(start_points)):
        start_point = start_points[i]
        end_point = end_points[i]
        macro_fission = macro_fissions[i]
        start_distance = np.sqrt((start_point[0] - start[0]) ** 2 + (start_point[1] - start[1]) ** 2)
        end_distance = np.sqrt((end_point[0] - start[0]) ** 2 + (end_point[1] - start[1]) ** 2)
        plt.plot([start_distance, end_distance], [macro_fission, macro_fission])

def build_shielded_geometry():
    air = Material(0.1, color='white')
    u235_metal = Material(1.0, 0.1, color='green')
    poly = Material(1.0, color='red')
    steel = Material(1.0, color='orange')

    box = create_hollow(create_rectangle(20., 10.), create_rectangle(18., 8.))

    hollow_circle = create_hollow(create_circle(3.9), create_circle(2.9))
    translate_rotate_mesh(hollow_circle, [-9 + 3.9 + 0.1, 0.])

    small_box_1 = create_rectangle(2., 2.)
    translate_rotate_mesh(small_box_1, [6., 2.])

    small_box_2 = create_rectangle(2., 2.)
    translate_rotate_mesh(small_box_2, [6., -2.])

    #sim = Simulation(air, 50., 45., 'arc')
    sim = Simulation(air, diameter=50.,)
    sim.detector.width = 30.
    sim.geometry.solids.append(Solid(box, steel, air))
    sim.geometry.solids.append(Solid(hollow_circle, u235_metal, air))
    sim.geometry.solids.append(Solid(small_box_1, poly, air))
    sim.geometry.solids.append(Solid(small_box_2, steel, air))
    sim.geometry.flatten()

    return sim

def ray_trace_test_geometry():
    air = Material(0.0, color='white')
    steel = Material(1.0, color='red')

    box = create_hollow(create_rectangle(12., 12.), create_rectangle(10., 10.))
    ring = create_hollow(create_circle(12.), create_circle(10.))
    translate_rotate_mesh(box, rotate = angle_matrix(45.))

    sim = Simulation(air, diameter=50.)
    sim.detector.width = 30.
    sim.geometry.solids.append(Solid(ring, steel, air))
    sim.geometry.flatten()

    return sim

def main():
    sim = build_shielded_geometry()

    plt.figure()
    sim.draw()

    angles = np.linspace(-15., 15., 20) * np.pi / 180.
    r = 100.
    start = sim.source

    for angle in angles:
        end = start + np.array([r * np.cos(angle), r * np.sin(angle)])

        segments, cross_sections = sim.fission_segments(start, end)

        for segment in segments:
            plt.plot([segment[0][0], segment[1][0]], [segment[0][1], segment[1][1]], color='black')

    plt.show()

if __name__ == "__main__":
    sys.exit(int(main() or 0))