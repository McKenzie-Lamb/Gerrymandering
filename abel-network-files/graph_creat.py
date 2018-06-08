# Author: Abel Gonzalez
# Date: 05/29/18
#
# Description:
# This program uses the .shp file to create a network graph where each node represents a census tract
# and the edge represents adjacency between each tract.

import fiona
import networkx as nx
import pygraphviz as pvg
from shapely.geometry import Polygon
from shapely.geometry import Point
import pyproj as proj

daShapefile = r"../Wards_fall_2014.shape/Wards_Final_Geo_111312_2014_ED.shp"

# Checks for adjacency between two shapes
# Inputs: Two polygons object
# Outputs: True for adjacency, False for not adjacency
def is_adjacent(shape1, shape2):
    return shape1.touches(shape2) and not isinstance(shape1.intersection(shape2),Point)

# Creates a shape object using the coordinates 
# provided by the .shp file
# Inputs: A .shp ring
# Output: the Polygon object
def get_poly(rings):
    for points in rings:
        ptlst = list(points)
        #In case there are not enough points to create a polygon
        if ptlst is None or len(ptlst) < 3:
            print("BAD!")
            continue
        poly = Polygon(ptlst)
        return poly

# Produces the color of the node based on republican and democrats share
# Input: tract that will be analyzed
# Output: Color of node
def get_color(feat):
    dem_vote = feat['properties']['CONDEM14']
    rep_vote = feat['properties']['CONREP14']

    if dem_vote == 0 and rep_vote == 0:
            color_n = '#FFFF0080'
    else:
        dem_share = dem_vote/(dem_vote+rep_vote)
        if dem_share > .5:
            alph = dem_share
            color_n = '#0000ff'+hex(int(alph*100))[2:]
        else :
            alph = (1-dem_share)
            color_n = '#ff0000'+hex(int(alph*100))[2:]
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
def get_position(x,y):
    old_min_x = 298550.4294446295
    old_max_x = 766195.0569210261
    old_range_x = old_max_x - old_min_x

    old_min_y =225691.9025871229
    old_max_y = 723701.7170331448
    old_range_y = old_max_y - old_min_y

    new_max = 100
    new_min = 0
    new_range = new_max - new_min
    new_x = (((x - old_min_x) * new_range)/old_range_x)
    new_y = (((y - old_min_y) * new_range)/old_range_y)

    return str(new_x)+','+str(new_y)+'!'
    

# Main for loop that reads the file, creates the graph,
# add nodes, and edges
with fiona.open(daShapefile) as shapes:
    graph = nx.Graph(directed=False)
    count = 0
    positions = []
    for feat in shapes: 
        properties = feat['properties']
        tract_id = feat['id']
        color_n = get_color(feat)
        rlist = get_rlist(feat)
        
        for rings in rlist:
            tracts = get_poly(rings)
        
        position = get_position(tracts.centroid.x,tracts.centroid.y)


        graph.add_node(tract_id,style = 'filled',shape = 'circle', pos=position, color=color_n, 
                    polygon = tracts, data=properties, fixedsize = True)
        count += 1
        latest_node = list(graph.nodes(data=False))[-1]
        for n in list(graph.nodes())[:count-1]:
            if is_adjacent(graph.node[n]['polygon'], graph.node[latest_node]['polygon']):
                graph.add_edge(n,latest_node)
            
A=nx.nx_agraph.to_agraph(graph)       # convert to a graphviz graph
A.write('data.dot')          # neato layout
