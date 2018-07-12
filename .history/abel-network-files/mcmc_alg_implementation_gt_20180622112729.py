# Author: Abel Gonzalez
# Date: 06/22/18
#
# Description:
# This program aims to implement the Markov Chain Montecarlo Simulation
# algorithm explained by Benjamin Fifield Michael Higgins Kosuke Imai
# and Alexander Tarr using graph tool
import gtk
import numpy as np
import graph_tool.all as gt
from pathlib import Path

data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

size_array = np.random.random([100,2])
graph, pos = gt.triangulation(size_array, type='delaunay')

gt.graph_draw(graph, pos=pos, bg_color=(255,255,255,1))
