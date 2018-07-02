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
                            vertex_bound = True
                            break
                    if vertex_bound == True:
                        label_boun += 1
                        break
            if label_boun == len(cp):
                cp_boundary.append(cp)
    return cp_boundary

def get_non_adjacent_v(labels_in_boundaries, graph):
    list_to_swap = random.sample(labels_in_boundaries, random.randint(2,len(labels_in_boundaries)//2))
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
            del list_to_swap[i]
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
        print(districts_graphs[i].graph_properties["dem_vote"])
        print(districts_graphs[i].graph_properties["rep_vote"])

def random_color():
    return (random.randint(1,255),random.randint(1,255),random.randint(1,255),1)

def adjust_color(districts_graphs):
    for i in range(len(districts_graphs)):
        ring_color_ = (random_color())
        if districts_graphs[i].graph_properties["dem_vote"] > districts_graphs[i].graph_properties["rep_vote"]:
            color_ = (0,0,255,1)
        else:
            color_ = (255,0,0,1)
        for v in districts_graphs[i].vertices():
            color[v] = color_
            ring_color[v] = ring_color_  


# Paths
main_folder = Path("abel-network-files/")
data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

# Loading the previous created Graph and creating the prop maps
graph = gt.load_graph(str(data_folder / "tmp_graph.gt"))
color = graph.new_vertex_property("vector<double>")
ring_color = graph.new_vertex_property("vector<double>")
cp_label = graph.new_vertex_property("int")

# Init variables
district_total_no = 2
gt.graph_draw(graph, pos=graph.vp.pos,
              output=str(main_folder / ('tmp.png')),
              bg_color=(255, 255, 255, 1), vertex_text=graph.vertex_index, 
              vertex_fill_color=color, vertex_color = ring_color)

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
                  turned_on_graphs[i], pos=graph.vp.pos,bg_color=(255,255,255,1),vertex_size=2,
                  output=str(main_folder / ('tmp1'+str(i)+'.png')), vertex_text=graph.vertex_index)

                  
labels_in_boundaries = get_cp_boundaries(graph, turned_on_graphs)
slected_vertices = get_non_adjacent_v(labels_in_boundaries, graph)
gather_districts_data(districts_graphs)
adjust_color(districts_graphs)
gt.graph_draw(graph, pos=graph.vp.pos,
              output=str(main_folder / ('tmp.png')),
              bg_color=(255, 255, 255, 1), vertex_text=graph.vertex_index, vertex_fill_color=color, vertex_color = ring_color)