# Author: Abel Gonzalez
# Date: 06/05/18
#
# Description:
# This program takes the previously created network graph and
# transfrom it into a grid by adding the census tracts properties

import networkx as nx
import pygraphviz as pvg
from scipy import spatial
import numpy as np

# Scales the coordinates from the shapely file to 0-100
# Inputs: x, y coordinates from shapely
# Ouputs: same value scaled to 0-100, in pygraphviz pos format
def get_position(x,y, total_nodes):
    old_min = 1
    old_max = total_nodes
    old_range = old_max - old_min

    new_max = 100
    new_min = 0
    new_range = new_max - new_min
    new_x = (((x - old_min) * new_range)/old_range)
    new_y = (((y - old_min) * new_range)/old_range)

    return str(new_x)+','+str(new_y)+'!'

# Takes a key and values from dictionary and loops through to get 
# weighted average or sum
def strip_data(dictionary_val):
    data = {}
    for i in dictionary_val:
        actual_dict = eval(i[7:].lower())
        for j in actual_dict.keys():
            if isinstance(actual_dict[j], str):
                continue
            if j in data:
                data[j] += actual_dict[j]
            else:
                data[j] = actual_dict[j]
    return data


# Creates the data that will be contained in the new nodes by averaging
# Inputs: the previously created graph
# Outputs: all the data
def add_data(grid_graph, wisconsin_graph, array):
    data = dict()
    for n in wisconsin_graph.nodes():
        point_pre = wisconsin_graph.node[n]['pos'][:-1].split(',')
        point_x = float(point_pre[0])
        point_y = float(point_pre[1])
        point = [point_x, point_y]
        #print(array)
        nearest_point_index = spatial.KDTree(array).query(point)[1]
        
        if nearest_point_index in data:
            data[nearest_point_index].append(wisconsin_graph.node[n]['data'])
        else:
            data[nearest_point_index] = [wisconsin_graph.node[n]['data']]
    for i in data.keys():
        if len(data[i]) > 1:
            grid_graph.node[str(i)]['data'] = strip_data(data[i])
    return grid_graph


# Main function that runs the whole project, and creates the .dot file
# Inputs: total number of x nodes
def main(nodes):
    wisconsin_graph = nx.Graph(nx.drawing.nx_agraph.read_dot('data.dot')) #Graph previously created
    grid_graph = nx.Graph(directed=False)
    total_nodes = nodes
    #array = np.empty([total_nodes**2, 2])
    list_positions = []
    count = 0
    for i in range(1,total_nodes): # This for loop creates the grid graph
        for j in range(1,total_nodes):

            #Node creation
            #label = str(i)+','+str(j)
            label = str(count)
            position = get_position(i, j, total_nodes)

            #np.array(array)[count,0] = float(position.split(',')[0])
            #np.array(array)[count,1] = float(position.split(',')[1][:-1])
            list_positions.append([float(position.split(',')[0]), float(position.split(',')[1][:-1])])
            #print(array)
            grid_graph.add_node(label, pos=position, shape='box', index = count)

            #This if statement creates the edges
            if i < 69 and j < 69:
                grid_graph.add_edge(label, str(i+1)+','+str(j))
                grid_graph.add_edge(label, str(i)+','+str(j+1))

            count+= 1
    array = np.asarray(list_positions)
    grid_graph = add_data(grid_graph, wisconsin_graph, array)
    
    A=nx.nx_agraph.to_agraph(grid_graph)       # convert to a graphviz graph
    A.write('grid_data.dot') 

main(70)