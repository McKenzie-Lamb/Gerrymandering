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
    selected_edges = dict()
    for district in range(len(districts_graphs)):
        selected = np.random.sample(districts_graphs[district])
    

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
                  bg_color=(255, 255, 255, 1), vertex_text=graph.vertex_index)
