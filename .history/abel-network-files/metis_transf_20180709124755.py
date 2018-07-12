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
color = graph.new_vertex_property('string')
adjlist_pop = []
nodew_pop = []

for i in graph.vertices():
    neighbors = tuple([j for j in i.all_neighbors()])
    adjlist_pop.append(neighbors)
    #print(graph.vp.data[i]['PERSONS'])
    weights = (graph.vp.data[i]['PERSONS'], graph.vp.data[i]['CONREP14']/graph.vp.data[i]['CONDEM14'])
    nodew_pop.append(weights)

metis_graph = metis.adjlist_to_metis(adjlist_pop, nodew=nodew_pop)
objval, parts = metis.part_graph(metis_graph, nparts=4)

for i in range(len(parts)):
    name[graph.vertex(i)] = parts[i]
    if graph.vp.data[graph.vertex(i)]['CONREP14'] > graph.vp.data[graph.vertex(i)]['CONDEM14']:
        color[graph.vertex(i)] = 'red'
    else:
        color[graph.vertex(i)] = 'blue'
gt.graph_draw(graph, pos=graph.vp.pos, vertex_text=name, output=str(main_folder / 'tmp_metis_init.png'))

adjlist = []
nodew = []

for i in graph.vertices():
    neighbors = tuple([j for j in i.all_neighbors()])
    adjlist.append(neighbors)
    #print(graph.vp.data[i]['PERSONS'])
    weights = (graph.vp.data[i]['PERSONS'], int(graph.vp.data[i]['CONREP14']/graph.vp.data[i]['CONDEM14']))
    nodew.append(weights)

metis_graph = metis.adjlist_to_metis(adjlist, nodew=nodew)
objval, parts = metis.part_graph(metis_graph, nparts=4, tpwgts=[(0.25,0.50),(0.25,0.10),(0.25, 0.30),(0.25, 0.10)])

for i in range(len(parts)):
    name[graph.vertex(i)] = parts[i]
    if graph.vp.data[graph.vertex(i)]['CONREP14'] > graph.vp.data[graph.vertex(i)]['CONDEM14']:
        color[graph.vertex(i)] = 'red'
    else:
        color[graph.vertex(i)] = 'blue'

gt.graph_draw(graph, pos=graph.vp.pos, vertex_text=name, output=str(main_folder / 'tmp_metis_fin.png'))