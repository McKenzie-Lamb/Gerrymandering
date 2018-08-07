# Author: Abel Gonzalez
# Date: 05/29/18
#
# Description:
# This program uses the .shp file to create a network graph where each node
# represents a census tract and the edge represents adjacency between each tract.

import fiona
import networkx as nx
from shapely.geometry import Polygon
from shapely.geometry import Point
import matplotlib.pyplot as plt
import random
import math
#Unix-like Path
#daShapefile = r"./Wards_fall_2014.shape/Wards_Final_Geo_111312_2014_ED.shp" 
#Windows path
daShapefile = r"E:\Projects\Gerrymandering\Gerrymandering\Drawing Wisconsin by Ward\Wards_fall_2014.shape\Wards_Final_Geo_111312_2014_ED.shp"

# Checks for adjacency between two shapes
# Inputs: Two polygons object
# Outputs: True for adjacency, False for not adjacency
def is_adjacent(shape1, shape2):
    return shape1.touches(shape2) and not isinstance(shape1.intersection(shape2),Point)

def is_adjacent_point_in(shape1, shape2):
    return shape1.touches(shape2)

# Creates a shape object using the coordinates 
# provided by the .shp file
# Inputs: A .shp ring
# Output: the Polygon object
def get_poly(rings):
    tracts = []
    for points in rings:
        ptlst = list(points)
        #In case there are not enough points to create a polygon
        if ptlst is None or len(ptlst) < 3:
            print("BAD!")
            continue
        poly = Polygon(ptlst)
        tracts += [poly]
    return tracts

# Produces the color of the node based on republican and democrats share
# Input: tract that will be analyzed
# Output: Color of node
def get_color(feat):
    dem_vote = feat['properties']['CONDEM14']
    rep_vote = feat['properties']['CONREP14']

    if dem_vote == 0 and rep_vote == 0:
            color_n = ()
    else:
        dem_share = dem_vote/(dem_vote+rep_vote)
        if dem_share > .5:
            alph = dem_share
            color_n = (0,0,1)
        else :
            alph = (1-dem_share)
            color_n = (1,0,0)
    return color_n

# Produces the r_list necessary to create th polygons
# Inputs: tract that will be analyzed
# Output: the r_list in a form of list
def get_rlist(feat):
    geom = feat["geometry"]
    if geom['type'] == "Polygon":
        rings = geom["coordinates"]
        rlist = [rings]
    elif geom['type'] == "MultiPolygon":
        rlist = geom["coordinates"]
    return rlist

# Scales the coordinates from the shapely file to 0-100
# Inputs: x, y coordinates from shapely
# Ouputs: same value scaled to 0-100, in pygraphviz pos format
def get_position(tracts):
    old_min_x = 298550.4294446295
    old_max_x = 766195.0569210261
    old_range_x = old_max_x - old_min_x

    old_min_y = 225691.9025871229
    old_max_y = 723701.7170331448
    old_range_y = old_max_y - old_min_y

    new_max = 100
    new_min = 0
    new_range = new_max - new_min
    
    centerx = 0
    centery = 0
    for i in tracts:
        x = i.centroid.x
        y = i.centroid.y
        centerx += (((x - old_min_x) * new_range)/old_range_x)
        centery += (((y - old_min_y) * new_range)/old_range_y)
        
    return centerx/len(tracts), centery/len(tracts)


def separate_properties(properties):
    pop = int(properties['PERSONS'])
    dem = int(properties['CONDEM14'])
    rep = int(properties['CONREP14'])
    try:
        dem_share = dem/(dem+rep)
    except ZeroDivisionError:
        dem_share = .5
    dem = math.floor(pop*dem_share)
    rep = pop - dem
    return [pop,dem,rep]


def clean_graph(graph):
    print("Cleaning...")
    nodes_to_del = []
    for i in nx.connected_components(graph):
        if len(i) < 27:
            for j in i:
                nodes_to_del.append(j)
    graph.remove_nodes_from(nodes_to_del)
    return graph

# Main for loop that reads the file, creates the graph,
# add nodes, and edges
with fiona.open(daShapefile) as shapes:
    graph = nx.Graph(directed=False)
    count = 0
    multycount = 0
    print("Creating Graph...")
    for feat in shapes:
        properties = feat['properties']
        tract_id = feat['id']
        color_n = get_color(feat)
        rlist = get_rlist(feat)
        
        tracts = []
        
        for rings in rlist:
            tracts += get_poly(rings)
            
        properties = separate_properties(properties)
        
        positionx, positiony = get_position(tracts)
        graph.add_node(int(tract_id), polygon=tracts, pop=properties[0], rep=properties[1], dem=properties[2], pos=(positionx, positiony), color=list(color_n))
        count += 1
        latest_node = list(graph.nodes(data=False))[-1]
        for n in list(graph.nodes())[:count-1]:
            for i in graph.node[n]['polygon']:
                for j in graph.node[latest_node]['polygon']:       
                    if is_adjacent(i, j):
                        graph.add_edge(n,latest_node)

print('Total Nodes - before cleaning: ', len(graph))
graph = clean_graph(graph)
print('Total Nodes - after cleaning: ', len(graph))
print(nx.is_connected(graph))
positions = dict()
color_map = []
for i in graph.nodes():
    positions[i] = (graph.node[i]['pos'])
    color_map.append((graph.node[i]['color']))

graph.graph['positions'] = positions

#small_graph = nx.ego_graph(graph, random.randint(1, len(graph)), radius=15)



nx.draw(graph, positions, node_size=(10))
nx.write_gpickle(graph, 'tmp.gpickle')
plt.savefig('tmp', dpi=300)