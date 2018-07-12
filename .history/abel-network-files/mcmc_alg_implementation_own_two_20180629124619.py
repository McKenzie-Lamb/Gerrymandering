# Author: Abel Gonzalez
# Date: 06/26/18
#
# Description:
# This program uses the .shp file to create a network graph where each node
# represents a census tract and the edge represents adjacency between each
# tract, usign graph-tool instead of networkx

import random
import numpy as np
import graph_tool.all as gt
from pathlib import Path

def create_graph_views(district_total_no):
    graph_views = list()
    for i in range(district_total_no):
        main_graph_view = gt.GraphView(graph)
        graph_view_check = main_graph_view.new_vertex_property("bool")
        matched_vertices = gt.find_vertex(graph, district_no, i)
        for j in matched_vertices:
            graph_view_check[j] = True
        graph_view = gt.GraphView(main_graph_view, vfilt=graph_view_check)
        graph_views.append(graph_view)
    return graph_views

def turn_off_edges(districts_graphs):
    turned_off_graphs = list()
    # Iterate through districts and selects random edges
    for district in range(len(districts_graphs)):
        to_delete = districts_graphs[district].new_edge_property('bool')
        edges = districts_graphs[district].get_edges()
        selected = edges[np.random.randint(edges.shape[0], size = len(edges)//3.5), :]
        for i in selected:
            to_delete[i] = True
        turned_off_graphs.append(gt.GraphView(districts_graphs[district], efilt=to_delete))
    return turned_off_graphs

def get_connected_components(main_graph, turned_off_graphs):
    cc_boun_v = dict()
    for g in turned_off_graphs:
        connected_components, hist = gt.label_components(g)
        for v in g.vertices():
            for n in main_graph.vertex(v).all_neighbors():
                if n in 


# Paths
main_folder = Path("abel-network-files/")
data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

# Loading the previous created Graph and creating the prop maps
graph = gt.load_graph(str(data_folder / "tmp_graph.gt"))
color = graph.new_vertex_property("vector<double>")
ring_color = graph.new_vertex_property("vector<double>")

# Init variables
district_total_no = 2
gt.graph_draw(graph, pos=graph.vp.pos,
              output=str(main_folder / ('tmp.png')),
              bg_color=(255, 255, 255, 1), vertex_text=graph.vertex_index)

# Separates graph into blocks
districts = gt.minimize_blockmodel_dl(graph, district_total_no, district_total_no)
district_no = districts.get_blocks()
districts.draw(output='tmp.png', vertex_text=graph.vertex_index)
# Create the different graphs
districts_graphs = create_graph_views(district_total_no)
for i in range(len(districts_graphs)):
    gt.graph_draw(
                  districts_graphs[i], pos=graph.vp.pos,
                  output=str(main_folder / ('tmp'+str(i)+'.png')),
                  bg_color=(255, 255, 255, 1))

turned_on_graphs = turn_off_edges(districts_graphs)
for i in range(len(districts_graphs)):
    gt.graph_draw(
                  turned_on_graphs[i], pos=graph.vp.pos,bg_color=(255,255,255,1),
                  output=str(main_folder / ('tmp1'+str(i)+'.png')), vertex_text=graph.vertex_index)

print(graph.vertex(1) in turned_on_graphs[0])

#cc_bound_vert = get_connected_components(main_graph, turned_on_graphs)
                  
