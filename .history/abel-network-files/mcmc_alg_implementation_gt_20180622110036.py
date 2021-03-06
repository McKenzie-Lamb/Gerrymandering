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

data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

size_array = np.ndarray(shape=(50,2), dtype=float, order='F')
graph = gt.complete_graph(50)

gt.graph_draw(graph,
              output='abel-network-files/tmp_alg.png', bg_color=(255,255,255,1))
