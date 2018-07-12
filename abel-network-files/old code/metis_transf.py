'''
Author: Abel Gonzalez
Date: 06/26/18

Description:
This program tries to use the metis package to do a districts distribution where 
the population of each distreicts is similar and the republican, democrats 
share are adjusted to maximize one or the other.
'''

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
district_no = graph.new_vertex_property('int')
adjlist_pop = []
nodew_pop = []

for i in graph.vertices():
    neighbors = tuple([j for j in i.all_neighbors()])
    adjlist_pop.append(neighbors)
    #print(graph.vp.data[i]['PERSONS'])
    weights = (graph.vp.data[i]['PERSONS'])
    nodew_pop.append(weights)

metis_graph = metis.adjlist_to_metis(adjlist_pop, nodew=nodew_pop)
objval, parts = metis.part_graph(metis_graph, nparts=4, contig=True, ufactor=99)

rep_dis = {p:0 for p in parts}
dem_dis = {p:0 for p in parts}
dis_v = {p:[] for p in parts}
pop = {p:0 for p in parts}
for i, p in enumerate(parts):
    rep_dis[p] += graph.vp.data[i]['CONREP14']
    dem_dis[p] += graph.vp.data[i]['CONDEM14']
    dis_v[p].append(graph.vertex(i))
    pop[p] += graph.vp.data[i]['PERSONS']

for p in dis_v.keys():
    if rep_dis[p] > dem_dis[p]:
        for v in dis_v[p]:
            color[graph.vertex(v)] = 'red'
    else:
        for v in dis_v[p]:
            color[graph.vertex(v)] = 'blue'

for i in range(len(parts)):
    name[graph.vertex(i)] = parts[i]
print(pop, dem_dis, rep_dis)
gt.graph_draw(graph, pos=graph.vp.pos, vertex_fill_color=color, vertex_text=name, output=str(main_folder / 'tmp_metis_init.png'), bg_color=(255,255,255,1))

adjlist = []
nodew = []

for i in graph.vertices():
    neighbors = tuple([j for j in i.all_neighbors()])
    adjlist.append(neighbors)
    #print(graph.vp.data[i]['PERSONS'])
    weights = (graph.vp.data[i]['PERSONS'], graph.vp.data[i]['CONREP14'], graph.vp.data[i]['CONDEM14'])
    nodew.append(weights)

metis_graph = metis.adjlist_to_metis(adjlist, nodew=nodew)
objval, parts = metis.part_graph(metis_graph, nparts=4, ufactor=99, tpwgts=[(0.25,0.50,0.25),(0.25,0.15,0.25),(0.25, 0.15,0.25),(0.25, 0.20, 0.25)], contig=True)

rep_dis = {p:0 for p in parts}
dem_dis = {p:0 for p in parts}
dis_v = {p:[] for p in parts}
pop = {p:0 for p in parts}
for i, p in enumerate(parts):
    rep_dis[p] += graph.vp.data[i]['CONREP14']
    dem_dis[p] += graph.vp.data[i]['CONDEM14']
    dis_v[p].append(graph.vertex(i))
    pop[p] += graph.vp.data[i]['PERSONS']

for p in dis_v.keys():
    if rep_dis[p] > dem_dis[p]:
        for v in dis_v[p]:
            color[graph.vertex(v)] = 'red'
    else:
        for v in dis_v[p]:
            color[graph.vertex(v)] = 'blue'

for i in range(len(parts)):
    name[graph.vertex(i)] = parts[i]
print(pop, dem_dis, rep_dis)
gt.graph_draw(graph, pos=graph.vp.pos, vertex_text=name, vertex_fill_color = color, output=str(main_folder / 'tmp_metis_fin.png'),bg_color=(255,255,255,1))