# Author: Abel Gonzalez
# Date: 06/26/18
#
# Description:
# This program uses the .shp file to create a network graph where each node
# represents a census tract and the edge represents adjacency between each
# tract, usign graph-tool instead of networkx
import random
import graph_tool.all as gt
from pathlib import Path


def get_districts_data(graph, color, blocks):
    # Assigning the district to each vertex as a property map
    districts_data = {}
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


def do_swap(graph, district_no, draw_no, ring_color_):
    # Swap edges group
    selected_nodes = dict()
    turned_on = list()
    for e in graph.vertices():
        value = random.randint(0,3)
        if value == 1:
            neighbors_list = list()
            border = False
            for neighbor in e.all_neighbors():
                neighbors_list.append(neighbor)
                if district_no[neighbor] != district_no[e]:
                    border = True
                    border_district = district_no[neighbor]
                    selected_nodes[e] = border_district
                    del neighbors_list[-1]
            if border == True:
                value_two = random.randint(0,1)
                if value_two == 1:
                    for i in neighbors_list:
                        value_three = random.randint(0,2)
                        if value_three == 1:
                            selected_nodes[i] = border_district
    for i in selected_nodes.keys():
        district_no[i] = selected_nodes[i]
        ring_color_[i] = (255, 255, 0, 1) if district_no[i] == 1 else (0, 255, 255, 1)

    adjust_color(get_districts_data(graph, color, districts), ring_color)
    gt.graph_draw(graph, bg_color=(255, 255, 255, 1), vertex_fill_color=ring_color, vertex_color=color, pos=graph.vp.pos,
              vertex_text=graph.vertex_index, output='abel-network-files/tmp'+str(draw_no)+'.png')
    return turned_on


# Paths
data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

# Loading the previous created Graph and creating the prop maps
graph = gt.load_graph(str(data_folder / "tmp_graph.gt"))
district_no = graph.new_vertex_property("int")
color = graph.new_vertex_property("vector<double>")
ring_color = graph.new_vertex_property("vector<double>")

# Separates graph into blocks
districts_vert_no = {}
districts = gt.minimize_blockmodel_dl(graph, 2,2)
adjust_color(get_districts_data(graph, color, districts), ring_color)
gt.graph_draw(graph, bg_color=(255, 255, 255, 1), vertex_fill_color=ring_color, vertex_color=color, pos=graph.vp.pos,
              vertex_text=graph.vertex_index, output='abel-network-files/tmp.png')
print()
do_swap(graph, district_no, 1, ring_color_)

