# Author: Abel Gonzalez
# Date: 06/18/18
#
# Description:
# This program uses the .shp file to create a network graph where each node represents a census tract
# and the edge represents adjacency between each tract, usign graph-tool instead of networkx

import fiona
import pyproj as proj
import graph_tool.all as gt
import random
from shapely.geometry import Polygon
from shapely.geometry import Point
import pprint

#Unix-like Path
daShapefile = r"./Wards_fall_2014.shape/Wards_Final_Geo_111312_2014_ED.shp"

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
            color_n = [255,255,0,0.5]
    else:
        dem_share = dem_vote/(dem_vote+rep_vote)
        if dem_share > .5:
            alph = dem_share
            color_n = [0,0,255,alph]
        else :
            alph = (1-dem_share)
            color_n = [255,0,0,alph]
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

    y = y*-1
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

    return (new_x,new_y)

with fiona.open(daShapefile) as shapes:
    pprint.pprint(shapes)
    graph = gt.Graph(directed=False)
    pos = graph.new_vertex_property("vector<double>")
    color = graph.new_vertex_property("vector<double>")
    data = graph.new_vertex_property("object")
    polygons = graph.new_vertex_property("object")
    index = 0
    polygons = dict()
    for feat in shapes:
        properties = eval(str(feat['properties'])[7:].lower())

        tract_id = int(feat['id'])

        color_n = get_color(feat)
        rlist = get_rlist(feat)

        for rings in rlist:
            tracts = get_poly(rings)
        
        polygons[index] = tracts
        tmp_position = get_position(tracts.centroid.x,tracts.centroid.y)

        vertex = graph.add_vertex()
        pos[vertex] = tmp_position
        data[vertex] = properties
        polygons[vertex] = tracts
        color[vertex] = get_color(feat)

        index += 1
        for i in graph.get_vertices()[:index-1]:
            if is_adjacent(polygons[i], polygons[vertex]):
                edge = graph.add_edge(i,vertex)

    graph.vertex_properties["color"] = color
    graph.vertex_properties["data"] = data
    gt.graph_draw(
                  graph, pos, vertex_text=graph.vertex_index
                  , vertex_fill_color=graph.vertex_properties["color"]
                  , output='abel-network-files/try.png'
                  , output_size=(2000,2000)
                  , vertex_halo = False
                  , vertex_font_size = .5)
    graph.save("abel-network-files/data/graph_creat.gt")