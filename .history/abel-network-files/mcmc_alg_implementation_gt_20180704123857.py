# Author: Abel Gonzalez
# Date: 06/24/18
#
# Description:
# This program aims to implement the Markov Chain Montecarlo Simulation
# algorithm explained by Benjamin Fifield Michael Higgins Kosuke Imai
# and Alexander Tarr using graph tool
import random
import time
import numpy as np
import graph_tool.all as gt
from pathlib import Path


def split_into_parts(number, n_parts):
    return np.linspace(0, number, n_parts+1)[1:-1]


def get_position(x, y, old_max_x, old_max_y, old_min_x, old_min_y):
    # Takes a x and y coordinate and transforms it into a scale between 0 and 100
    # Inputs: tuple of x and y
    # Outputs: tuple of the x and y between 0 and 100

    y = y*-1
    old_range_x = old_max_x - old_min_x

    old_range_y = old_max_y - old_min_y

    new_max = 100
    new_min = 0
    new_range = new_max - new_min
    new_x = (((x - old_min_x) * new_range)/old_range_x)
    new_y = (((y - old_min_y) * new_range)/old_range_y)
    return (new_x, new_y)

def draw_grap(state):
    state.draw(pos=graph.vp.pos, output="abel-network-files/tmp/d"+str(time.time())+".png")

data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

size_array = np.random.random([50, 2])
graph, pos = gt.triangulation(size_array, type='delaunay')
data = graph.new_vertex_property("object")
color = graph.new_vertex_property("vector<double>")
maxx = 0
maxy = 0
minx = 100
miny = 100
for v in graph.vertices():
    if (pos[v][0]) > maxx:
        maxx = pos[v][0]
    if (pos[v][0]) < minx:
        minx = pos[v][0]
    if (pos[v][1]) > maxy:
        maxy = pos[v][1]
    if (pos[v][1]) < miny:
        miny = pos[v][1]
#Change coordinates range to match previous graphs,
#this will not be necessary once we have the real graph
for v in graph.vertices():
    pos[v] = get_position(pos[v][0], pos[v][1], minx, miny, maxx, maxy)
    pop = random.randint(500,1000)
    rep = random.randint(0,pop)
    data[v] = {'CONREP14': rep, 'CONDEM14': pop-rep, 'PERSONS': pop}
graph.vp.pos = pos
graph.vp.data = data
state = gt.minimize_blockmodel_dl(graph, 2,2)
gt.mcmc_equilibrate(state, callback=draw_grap, mcmc_args={'niter':2}, max_niter=20)

state.draw(pos=graph.vp.pos, output="abel-network-files/tmp_alg_states.png")
gt.graph_draw(graph, pos, output="abel-network-files/tmp_alg.png", bg_color=(255,255,255,1))
graph.save("abel-network-files/data/tmp_graph50.gt")