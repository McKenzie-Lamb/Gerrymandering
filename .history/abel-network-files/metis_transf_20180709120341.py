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
name = graph.new_vertex_property('string')

adjlist = []
nodew = []

for i in graph.vertices():
    neighbors = tuple([j for j in i.all_neighbors()])
    adjlist.append(neighbors)
    #print(graph.vp.data[i]['PERSONS'])
    nodew.append(graph.vp.data[i]['PERSONS'])

metis_graph = metis.adjlist_to_metis(adjlist, nodew=nodew)
objval, parts = metis.part_graph(metis_graph, nparts=4)

for i in range(len(parts)):
    name[graph.vertex(i)] = parts[i]


gt.GraphWindow(graph, vertex_text=name)