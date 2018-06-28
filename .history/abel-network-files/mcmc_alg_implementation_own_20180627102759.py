# Author: Abel Gonzalez
# Date: 06/26/18
#
# Description:
# This program uses the .shp file to create a network graph where each node
# represents a census tract and the edge represents adjacency between each
# tract, usign graph-tool instead of networkx

import graph_tool.all as gt
from pathlib import Path


def get_districts_data(graph, color):
    # Assigning the district to each vertex as a property map
    districts_data = {}
    districts = gt.minimize_blockmodel_dl(graph, 2,2)
    blocks = districts.get_blocks()
    for i in graph.vertices():
        district_no[graph.vertex(i)] = blocks[i]
        color[graph.vertex(i)] = (255, 255, 0, 1) if blocks[i] == 1 else (0, 255, 255, 1)
        if district_no[graph.vertex(i)] in districts_data.keys():
            for j in districts_data[blocks[i]].keys():
                districts_data[blocks[i]][j] += graph.vp.data[i][j]
        else:
            districts_data[blocks[i]] = graph.vp.data[i]
    return districts_data


def adjust_color(districts_data, ring_color):
    # Assign ring color based on democrats total votes:
    for i in districts_data.keys():
        if districts_data[i]['CONDEM14'] > districts_data[i]['CONREP14']:
            ring_color_ = (0, 0, 255, 1)
        else:
            ring_color_ = (255, 0, 0, 1)
        matched_vertices = gt.find_vertex(graph, district_no, i)
        for j in matched_vertices:
            ring_color[graph.vertex(j)] = ring_color_

# Paths
data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

# Loading the previous created Graph and creating the prop maps
graph = gt.load_graph(str(data_folder / "tmp_graph.gt"))
district_no = graph.new_vertex_property("int")
color = graph.new_vertex_property("vector<double>")
ring_color = graph.new_vertex_property("vector<double>")

adjust_color(get_districts_data(graph, color), ring_color)

print(len(graph.get_vertices())

gt.graph_draw(graph, bg_color=(255, 255, 255, 1), vertex_fill_color=ring_color, vertex_color=color, pos=graph.vp.pos,
              vertex_text=graph.vertex_index, output='abel-network-files/tmp.png')
