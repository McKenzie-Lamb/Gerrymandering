# Author: Abel Gonzalez
# Date: 06/26/18
#
# Description:
# This program uses the .shp file to create a network graph where each node
# represents a census tract and the edge represents adjacency between each
# tract, usign graph-tool instead of networkx
import random
import math
import numpy as np
import graph_tool.all as gt
from pathlib import Path


def create_graph_views(district_total_no):
    graph_views = list()
    for i in range(district_total_no):
        graph_view = gt.GraphView(graph)
        graph_view_check = graph_view.new_vertex_property("bool")
        matched_vertices = gt.find_vertex(graph, district_no, i)
        for j in matched_vertices:
            graph_view_check[j] = True
        graph_view = gt.GraphView(graph_view, vfilt=graph_view_check)
        graph_view.vp.valid = graph_view_check
        graph_views.append(graph_view)
    return graph_views


def turn_off_edges(districts_graphs):
    turned_off_graphs = list()
    # Iterate through districts and selects random edges
    for district in range(len(districts_graphs)):
        to_delete = districts_graphs[district].new_edge_property('bool')
        edges = districts_graphs[district].get_edges()
        selected = edges[np.random.randint(
            edges.shape[0], size=len(edges)//3.5), :] # Here is the prob for edge turn off
        for i in selected:
            to_delete[i] = True
        turned_off_graphs.append(gt.GraphView(
            districts_graphs[district], efilt=to_delete))
    return turned_off_graphs


def get_cp_boundaries(graph, turned_on_graphs):
    cp_boundary = list()
    for g in range(len(turned_on_graphs)):
        cp_label, hist = gt.label_components(turned_on_graphs[g])
        labels = set(cp_label.a)
        for l in labels:
            cp = gt.find_vertex(turned_on_graphs[g], cp_label, l)
            label_boun = 0
            for v in cp:
                vertex_bound = False
                for n in graph.vertex(v).all_neighbors():
                    for g_two in range(len(turned_on_graphs)):
                        if g == g_two:
                            continue
                        try:
                            turned_on_graphs[g_two].vertex(n)
                        except ValueError:
                            continue
                        else:
                            graph.vp.nd[graph.vertex(v)] = g_two
                            graph.vp.cd[graph.vertex(v)] = g
                            vertex_bound = True
                            break
                    if vertex_bound == True:
                        label_boun += 1
                        break
            if label_boun == len(cp):
                cp_boundary.append(cp)
    return cp_boundary


def get_non_adjacent_v(labels_in_boundaries, graph):
    list_to_swap = random.sample(
        labels_in_boundaries, random.randint(2, (2*len(labels_in_boundaries))//3)) # Prob for choosing from boundaries
    index_to_del = list()
    for l in range(len(list_to_swap)):
        for v in range(len(list_to_swap[l])):
            for l_two in range(len(list_to_swap)):
                if l == l_two:
                    continue
                for v_two in range(len(list_to_swap[l_two])):
                    if len(gt.shortest_path(graph, graph.vertex(list_to_swap[l][v]), graph.vertex(list_to_swap[l_two][v_two]))[0]) < 3:
                        index_to_del.append(l)
    for i in range(len(list_to_swap)):
        if i in index_to_del:
            try:
                del list_to_swap[i]
            except IndexError:
                print("Empty, Reapeating")
                get_non_adjacent_v(labels_in_boundaries, graph)
    return list_to_swap


def gather_districts_data(districts_graphs):
    for i in range(len(districts_graphs)):
        population = districts_graphs[i].new_graph_property('int')
        districts_graphs[i].graph_properties["pop"] = population
        districts_graphs[i].graph_properties["pop"] = 0
        dem_vote = districts_graphs[i].new_graph_property('int')
        districts_graphs[i].graph_properties["dem_vote"] = dem_vote
        districts_graphs[i].graph_properties["dem_vote"] = 0
        rep_vote = districts_graphs[i].new_graph_property('int')
        districts_graphs[i].graph_properties["rep_vote"] = rep_vote
        districts_graphs[i].graph_properties["rep_vote"] = 0
        for v in districts_graphs[i].vertices():
            districts_graphs[i].graph_properties["pop"] += graph.vp.data[v]["PERSONS"]
            districts_graphs[i].graph_properties["dem_vote"] += graph.vp.data[v]["CONDEM14"]
            districts_graphs[i].graph_properties["rep_vote"] += graph.vp.data[v]["CONREP14"]
    return districts_graphs

def random_color():
    r = random.randint(0, 256)
    g = random.randint(0, 256)
    b = random.randint(0, 256)
    a = 1
    color_to_return = [r, g, b, a]
    index_to_zero = random.randint(0, 3)
    color_to_return[index_to_zero] = 0
    return color_to_return


def adjust_color(districts_graphs, color, ring_color, niter_type = 'first', ring_colors_dict = None):
    if niter_type == 'nonfirst':
        for i in range(len(districts_graphs)):
            if districts_graphs[i].graph_properties["dem_vote"] > districts_graphs[i].graph_properties["rep_vote"]:
                color_ = (0, 0, 255, 1)
            else:
                color_ = (255, 0, 0, 1)
            for v in districts_graphs[i].vertices():
                color[v] = color_
                ring_color[v] = ring_colors_dict[i]
        return color, ring_color

    else:
        ring_colors_dict = dict()
        for i in range(len(districts_graphs)):
            ring_color_to = random_color()
            ring_colors_dict[i] = ring_color_to
            if districts_graphs[i].graph_properties["dem_vote"] > districts_graphs[i].graph_properties["rep_vote"]:
                color_ = (0, 0, 255, 1)
            else:
                color_ = (255, 0, 0, 1)
            for v in districts_graphs[i].vertices():
                color[v] = color_
                ring_color[v] = ring_color_to
        return color, ring_color, ring_colors_dict


def propose_swap(districts_graphs, proposed_components, graph, labels_in_boundaries):
    changes = dict()
    vertex_to_add = dict()
    vertex_to_delete = dict()
    for i in range(len(districts_graphs)):
        changes[i] = [districts_graphs[i].graph_properties["pop"],
                      districts_graphs[i].graph_properties["rep_vote"],
                      districts_graphs[i].graph_properties["dem_vote"]]
        vertex_to_add[i] = []
        vertex_to_delete[i] = []
    for c in proposed_components:
        added_pop = 0
        added_rep = 0
        added_dem = 0
        n_dindex = 0
        c_dindex = 0
        for v in range(len(c)):
            added_pop += graph.vp.data[c[v]]['PERSONS']
            added_rep += graph.vp.data[c[v]]['CONREP14']
            added_dem += graph.vp.data[c[v]]['CONDEM14']
            n_dindex = graph.vp.nd[c[v]]
            c_dindex = graph.vp.cd[c[v]]
            vertex_to_add[n_dindex].append(c[v])
            vertex_to_delete[c_dindex].append(c[v])
        changes[n_dindex][0] += added_pop
        changes[n_dindex][1] += added_rep
        changes[n_dindex][2] += added_dem
        changes[c_dindex][0] -= added_pop
        changes[c_dindex][1] -= added_rep
        changes[c_dindex][2] -= added_dem
    similar_pop = True
    for i in changes.keys():
        if i == 0:
            continue
        print(changes[i][0])
        print(changes[i-1][0])
        similar_pop = math.isclose(changes[i][0], changes[i-1][0], rel_tol=0.30)
    if similar_pop == True:
        print("Similar pop")
        for i in changes.keys():
            districts_graphs[i].graph_properties["pop"] += changes[i][0]
            districts_graphs[i].graph_properties["rep_vote"] += changes[i][1]
            districts_graphs[i].graph_properties["dem_vote"] += changes[i][2]
            for j in vertex_to_add[i]:
                if len(vertex_to_add[i]) == 0:
                    break
                districts_graphs[i].vp.valid[j] = True
            for j in vertex_to_delete[i]:
                if len(vertex_to_delete[i]) == 0:
                    break
                districts_graphs[i].vp.valid[j] = False
            districts_graphs[i] = gt.GraphView(districts_graphs[i], vfilt = districts_graphs[i].vp.valid)



    if similar_pop == False:
        print("Pop differ")
        selected_vertices = get_non_adjacent_v(labels_in_boundaries, graph)
        propose_swap(districts_graphs, selected_vertices, graph, labels_in_boundaries)


# Paths
main_folder = Path("abel-network-files/")
data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

# Loading the previous created Graph and creating the prop maps
graph = gt.load_graph(str(data_folder / "tmp_graph.gt"))
color = graph.new_vertex_property("vector<double>")
ring_color = graph.new_vertex_property("vector<double>")
cp_label = graph.new_vertex_property("int")
neighbor_district = graph.new_vertex_property('int')
current_district = graph.new_vertex_property('int')
graph.vp.nd = neighbor_district
graph.vp.cd = current_district

# Init variables
district_total_no = 2

# Separates graph into blocks
districts = gt.minimize_blockmodel_dl(
    graph, district_total_no, district_total_no)
district_no = districts.get_blocks()

# Create the different graphs
districts_graphs = create_graph_views(district_total_no)

# Initialize data and draw first image
districts_graphs = gather_districts_data(districts_graphs)
color, ring_color, ring_colors_dict = adjust_color(districts_graphs, color, ring_color)
gt.graph_draw(graph, vertex_fill_color = color, vertex_color = ring_color,
              output = str(main_folder / 'tmp.png'), bg_color=(255, 255, 255, 1), pos=graph.vp.pos)


# Actual function calling part of algorithm
for i in range(100):
    turned_on_graphs = turn_off_edges(districts_graphs)
    labels_in_boundaries = get_cp_boundaries(graph, turned_on_graphs)
    selected_vertices = get_non_adjacent_v(labels_in_boundaries, graph)
    propose_swap(districts_graphs, selected_vertices, graph, labels_in_boundaries)
    adjust_color(districts_graphs, color, ring_color, niter_type = 'nonfirst', ring_colors_dict = ring_colors_dict)
    print('Drawing')
    gt.graph_draw(graph, vertex_fill_color = color, vertex_color = ring_color,
              output = str(main_folder / ('tmp'+str(i)+'.png')), bg_color=(255, 255, 255, 1), pos=graph.vp.pos)


