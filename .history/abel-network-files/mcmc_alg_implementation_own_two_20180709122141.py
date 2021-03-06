# Author: Abel Gonzalez
# Date: 06/26/18
#
# Description:
# This program uses the .shp file to create a network graph where each node
# represents a census tract and the edge represents adjacency between each
# tract, usign graph-tool instead of networkx
import random
import copy
import metis
import math
import numpy as np
import graph_tool.all as gt
import time
from pathlib import Path


def gen_initial_distribution(graph, district_no):
    # Uses the metis package to create a graph partition whose initial values
    # of population are similar
    # IPUTS: graph to be partitioned and property map with 
    # OUTPUTS: 
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
        district_no[graph.vertex(i)] = parts[i]
    return graph, district_no


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
            edges.shape[0], size=random.randint((len(edges)//2), 2*len(edges)//3)), :] # Here is the prob for edge turn off
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
        labels_in_boundaries, random.randint(len(labels_in_boundaries)//3, len(labels_in_boundaries)//2)) # Prob for choosing from boundaries
    index_to_del = set()
    # for l in range(len(list_to_swap)):
    #     for v in range(len(list_to_swap[l])):
    #         for l_two in range(len(list_to_swap)):
    #             if l == l_two:
    #                 continue
    #             for v_two in range(len(list_to_swap[l_two])):
    #                 if len(gt.shortest_path(graph, graph.vertex(list_to_swap[l][v]), graph.vertex(list_to_swap[l_two][v_two]))[0]) < 3:
    #                     index_to_del.add(l_two)
    # for i in range(len(list_to_swap)):
    #     print(list_to_swap)
    #     if i in index_to_del:
    #         try:
    #             del list_to_swap[i]
    #         except IndexError:
    #             print('list empty')
    #             continue
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
    colors_list = ['black','silver','firebrick','sienna', 'gold', ]
    r = random.uniform(0, 1)
    g = random.uniform(0, 1)
    b = random.uniform(0, 1)
    a = 1
    color_to_return = [r, g, b, a]
    return color_to_return


def adjust_color(districts_graphs, color, ring_color, district_of_vertex, niter_type = 'first', ring_colors_dict = None):
    if niter_type == 'nonfirst':
        for i in range(len(districts_graphs)):
            if districts_graphs[i].graph_properties["dem_vote"] > districts_graphs[i].graph_properties["rep_vote"]:
                color_ = 'blue'
            else:
                color_ = 'red'
            for v in districts_graphs[i].vertices():
                color[v] = color_
                ring_color[v] = ring_colors_dict[i]
                district_of_vertex[v] = i
        return color, ring_color
    elif niter_type == 'first':
        ring_colors_dict = dict()
        for i in range(len(districts_graphs)):
            ring_colors_dict[i] = random_color().copy()
            if districts_graphs[i].graph_properties["dem_vote"] > districts_graphs[i].graph_properties["rep_vote"]:
                color_ = 'blue'
                #color_ = to_color
            else:
                color_ = 'red'
                #color_ = to_color
            for v in districts_graphs[i].vertices():
                color[v] = color_
                ring_color[v] = ring_colors_dict[i]
                district_of_vertex[v] = i
        return color, ring_color, ring_colors_dict


def propose_swap(districts_graphs, proposed_components, graph, labels_in_boundaries, actual_swaps):
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
        similar_pop = math.isclose(changes[i][0], changes[i-1][0], rel_tol=0.20) # Here is the population difference
    if similar_pop == True:
        contiguos = True
        # Check for contiguity
        d_copy = copy.deepcopy(districts_graphs)
        for i in range(len(districts_graphs)):
            for j in vertex_to_add[i]:
                #if len(vertex_to_add[i]) == 0:
                #    break
                districts_graphs[i].vp.valid[j] = True
                #previous_graph.vp.valid[j] = True
            for j in vertex_to_delete[i]:
                #if len(vertex_to_delete[i]) == 0:
                #    break
                districts_graphs[i].vp.valid[j] = False
                #previous_graph[j] = False
            components_check, hist = gt.label_components(districts_graphs[i])
            if np.sum(components_check.a) != 0:
                contiguos = False
                break
        if contiguos == True:
            # Change Data
            for i in changes.keys():
                districts_graphs[i].graph_properties["pop"] = changes[i][0]
                districts_graphs[i].graph_properties["rep_vote"] = changes[i][1]
                districts_graphs[i].graph_properties["dem_vote"] = changes[i][2]
            actual_swaps += 1
            return districts_graphs, actual_swaps
        else:
            districts_graphs = d_copy
            return districts_graphs, actual_swaps
    else:
        return districts_graphs, actual_swaps


print('Initialazing...')
# Paths
main_folder = Path("abel-network-files/")
data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

# Loading the previous created Graph and creating the prop maps
graph = gt.load_graph(str(data_folder / "tmp_graph1000.gt"))
color = graph.new_vertex_property("string")
ring_color = graph.new_vertex_property("vector<float>")
cp_label = graph.new_vertex_property("int")
neighbor_district = graph.new_vertex_property('int')
current_district = graph.new_vertex_property('int')
district_of_vertex = graph.new_vertex_property('int')
district_no = graph.new_vertex_property('int')
graph.vp.nd = neighbor_district
graph.vp.cd = current_district

# Init variables
district_total_no = 4
swaps_to_try = 10

# # Separates graph into blocks
 districts = gt.minimize_blockmodel_dl(
#     graph, district_total_no, district_total_no)
 district_no = districts.get_blocks()


# Create the different graphs
#graph, district_no = gen_initial_distribution(graph, district_no)
districts_graphs = create_graph_views(district_total_no)

# Initialize data and draw first image
districts_graphs = gather_districts_data(districts_graphs)
color, ring_color, ring_colors_dict = adjust_color(districts_graphs, color, ring_color, district_of_vertex)
dem_seats = 0
rep_seats = 0
actual_swaps = 0
for i in districts_graphs:
    if i.graph_properties["dem_vote"] > i.graph_properties["rep_vote"]:
        dem_seats += 1
    else:
        rep_seats += 1
gt.graph_draw(graph, vertex_color = ring_color, vertex_fill_color = color, vertex_text = district_of_vertex,
              output = str(main_folder / ('tmp.png')), bg_color=(255, 255, 255, 1), pos=graph.vp.pos)


print('Swapping census tracts...')
start = time.time()
#Actual function calling part of algorithm
for i in range(swaps_to_try):
    print(i)
    turned_on_graphs = turn_off_edges(districts_graphs)
    labels_in_boundaries = get_cp_boundaries(graph, turned_on_graphs)
    selected_vertices = get_non_adjacent_v(labels_in_boundaries, graph)
    districts_graphs, actual_swaps = propose_swap(districts_graphs, selected_vertices, graph, labels_in_boundaries, actual_swaps)
    #color, ring_color = adjust_color(districts_graphs, color, ring_color, niter_type = 'nonfirst', ring_colors_dict = ring_colors_dict)
    #gt.graph_draw(graph, vertex_color = ring_color, vertex_fill_color = color,
    #              output = str(main_folder / ('tmp'+str(i)+'.png')), bg_color=(255, 255, 255, 1), pos=graph.vp.pos)
end = time.time()
print('DONE')
print()

dem_seats_f = 0
rep_seats_f = 0
for i in districts_graphs:
    if i.graph_properties["dem_vote"] > i.graph_properties["rep_vote"]:
        dem_seats_f += 1
    else:
        rep_seats_f += 1
color, ring_color, ring_colors_dict = adjust_color(districts_graphs, color, ring_color, district_of_vertex)
gt.graph_draw(graph, vertex_color = ring_color, vertex_fill_color = color, vertex_text = district_of_vertex,
              output = str(main_folder / ('tmpf.png')), bg_color=(255, 255, 255, 1), pos=graph.vp.pos)

print('Statistics:')
print('-----------')
print('Total Number of districts:', district_total_no)
print('Dem Seats:', dem_seats,'-',dem_seats_f) #Initial, final
print('Rep Seats:', rep_seats,'-',rep_seats_f)
print('Swaps:', swaps_to_try, actual_swaps) #Tried, actuald swaps done
print('Time for swaps:', end - start)
