# Author: Abel Gonzalez
# Date: 06/26/18
#
# Description:
# This program uses the .shp file to create a network graph where each node
# represents a census tract and the edge represents adjacency between each
# tract, usign graph-tool instead of networkx

import graph_tool.all as gt
import metis
from pathlib import Path

# Paths
main_folder = Path("abel-network-files/")
data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

# Loading the previous created Graph and creating the prop maps
graph = gt.load_graph(str(data_folder / "tmp_graph100.gt"))

adjlist = []
nodew = []

for i in graph.vertices():
    neighbors = tuple([j for j in i.all_neighbors()])
    adjlist.append(neighbors)
    print(graph.vp.data['PERSONS'])
    nodew.append(graph.vp.data['PERSONS'])
