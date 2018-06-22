# Author: Abel Gonzalez
# Date: 06/05/18
#
# Description:
# This program takes the previously created network graph and
# transfrom it into a grid by adding the census tracts properties
# the number of nodes inside the graph can be changed by calling
# main function with a different value, this will not change the overall
# size of the function, more like the number of nodes contained in the
# inside using graph_tool instead of networkx

import numpy as np
import graph_tool.all as gt
from scipy import spatial
# Takes a x and y coordinate and transforms it into a scale between 0 and 100
# Inputs: tuple of x and y
# Outputs: tuple of the x and y between 0 and 100


def get_position(x, y, old_max_x, old_max_y):
    y = y*-1
    old_min_x = 0
    old_range_x = old_max_x - old_min_x

    old_min_y = 0
    old_range_y = old_max_y - old_min_y

    new_max = 100
    new_min = 0
    new_range = new_max - new_min
    new_x = (((x - old_min_x) * new_range)/old_range_x)
    new_y = (((y - old_min_y) * new_range)/old_range_y)
    return (new_x, new_y)


# Takes a key and values from dictionary and loops through to get 
# weighted average or sum
def sum_data(old_dict, new_dict):
    return_dict = dict()
    for i in old_dict.keys():
        if isinstance(old_dict[i], str):
            continue
        return_dict[i] = old_dict[i] + new_dict[i]
    return return_dict


# Creates the data that will be contained in the new nodes by averaging
# Inputs: grid graph and wisconsin graph
# Outputs: all the data
def add_data(grid, data, wisconsin_graph, array):
    check = []
    for n in wisconsin_graph.vertices():
        point = wisconsin_graph.vp.pos[n]
        nearest_point_index = spatial.KDTree(array).query(point)[1]
        
        vertex_data_wi = wisconsin_graph.vp.data[n]
        if nearest_point_index in check:
            data[grid.vertex(nearest_point_index)] = sum_data(data[grid.vertex(nearest_point_index)], vertex_data_wi)
        else:
            data[grid.vertex(nearest_point_index)] = vertex_data_wi

        check.append(nearest_point_index)
    return data


def main(x,y):
    x_total_ver = x
    y_total_ver = y
    grid = gt.lattice([x_total_ver, y_total_ver])
    wi_graph = gt.load_graph("graph_creat.gt")
    data = grid.new_vertex_property("object")
    positions = grid.new_vertex_property("vector<double>")
    index = 0
    points_array = list()
    for i in range(0, x_total_ver):
        for j in range(0, y_total_ver):
            points_array.append(get_position(i, j, x_total_ver, y_total_ver))
            positions[grid.vertex(index)] = points_array[-1]
            index += 1
    points_array = np.asarray(points_array)

    data = add_data(grid, data, wi_graph, points_array)
    grid.vertex_properties["data"] = data
    gt.graph_draw(grid, output_size=(3000, 3000)
                  , output="tmp_grid.png")


main(70, 70)

