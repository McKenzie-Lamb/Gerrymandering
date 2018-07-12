# Author: Abel Gonzalez
# Date: 06/22/18
#
# Description:
# This program aims to implement the Markov Chain Montecarlo Simulation
# algorithm explained by Benjamin Fifield Michael Higgins Kosuke Imai
# and Alexander Tarr using graph tool

import numpy as np
import graph_tool.all as gt
from pathlib import Path


def get_position(x, y, old_max_x, old_max_y):
    # Takes a x and y coordinate and transforms it into a scale between 0 and 100
    # Inputs: tuple of x and y
    # Outputs: tuple of the x and y between 0 and 100

    y = y*-1
    old_min_x = 0
    old_range_x = old_max_x - old_min_x

    old_min_y = 0
    old_range_y = old_max_y - old_min_y

    new_max = 100
    new_min = 0
    new_range = new_max - new_min
    new_x = (((x - old_min_x) * new_range)/old_range_x)
    new_y = (((y - old_min_y) * new_range)/old_range_y)
    return (new_x, new_y)

def main():
    data_folder = Path("abel-network-files/data/")
    images_folder = Path("abel-network-files/images/")

    size_array = np.random.random([100,2])
    graph, pos = gt.triangulation(size_array, type='delaunay')
    maxx = 0
    maxy = 0
    for i in pos:
        if pos[i][0] > float(maxx):
            maxx = pos[0]
        if pos[i][1] > float(maxy):
            maxy = pos[1]
    print(maxx, maxy)
    #Change coordinates range to match previous graphs,
    #this will not be necessary once we have the real graph
    for v in graph.vertices():
        pos[v] = get_position(pos[v][0], pos[v][1], )
    print(pos[graph.vertex(0)])

    gt.graph_draw(graph, pos, output="abel-network-files/tmp_alg.png", bg_color=(255,255,255,1))

main()