# Author: Abel Gonzalez
# Date: 06/12/18
#
# Description:
# This program aims to implement the Markov Chain Montecarlo Simulation
# algorithm explained by Benjamin Fifield Michael Higgins Kosuke Imai
# and Alexander Tarr
#%%
import pprint
import networkx as nx
import random

def create_xy(xy_string):
    splitted = xy_string.split(',')
    x = splitted[0]
    y = splitted[1][:-1]
    return [x,y]
#%%
# Produces a random graph to use this algorithm for quicker bug repair
# Output: a networkx graphw
def create_graph():
    tmp_graph = nx.Graph(nx.drawing.nx_pydot.read_dot('e:/Projects/Gerrymandering/Gerrymandering/abel-network-files/data/short_data.dot'))
    new_graph = nx.Graph()
    new_graph.add_nodes_from(tmp_graph.nodes(data=True))
    for n in new_graph.nodes():
        random_x = random.uniform(1,20)
        random_y = random.uniform(1,20)
        random_position = str(random_x) +',' + str(random_y) + '!'
        new_graph.node[n]['pos'] = random_position
        new_graph.node[n]['fontsize'] = 4
        new_graph.node[n]['fixedsize'] = True
        new_graph.node[n]['width'] = .3
        new_graph.node[n]['height'] = .3
    for n in new_graph.nodes():
        position_n = new_graph.node[n]['pos']
        position_n = create_xy(position_n)
        for i in new_graph.nodes():
            if n == i:
                continue 
            position_i = new_graph.node[i]['pos']
            position_i = create_xy(position_i)
            distance_x = abs(float(position_n[0]) - float(position_i[0]))
            distance_y = abs(float(position_n[1]) - float(position_i[1]))
            if distance_x < 1 and distance_y < 1:
                new_graph.add_edge(n,i)
    return new_graph
new_graph = create_graph()
#%%
def random_hex():
    _HEX = list('0123456789ABCDEF')
    return '#' + ''.join(_HEX[random.randint(0, len(_HEX)-1)] for _ in range(6))

# This function creates the dot_file for ease on debuging
# Input: Graph and name
# Outputs: None
def draw_graph(graph, name): 
    nx.drawing.nx_pydot.write_dot(graph, 'e:/Projects/Gerrymandering/Gerrymandering/abel-network-files/data/mcmc_' + str(name) + '.dot')

def divide_graph(graph, no_districts, max_xy):
    limit = int(max_xy/(no_districts/2))
    steps = [i for i in range(0,max_xy+1, limit)]    
    x_limits = []
    y_limits = []
    for i in range(len(steps)):
        if i == len(steps)-1:
            break
        x_limits.append((steps[i], steps[i+1]))
        y_limits.append((steps[i], steps[i+1]))

    districts_nodes = {}
    districts = {}
    for x in x_limits:
        for y in y_limits:
            districts_nodes[str(x)+str(y)] = []

    for n in graph.nodes():
        n_pos = create_xy(graph.node[n]['pos'])
        for x in x_limits:
            if float(n_pos[0]) > x[0] and float(n_pos[0]) < x[1]:
                for y in y_limits:
                    if float(n_pos[1]) > y[0] and float(n_pos[1]) < y[1]:
                        districts_nodes[str(x)+str(y)].append(n)
    
    for i in districts_nodes.keys():
        districts[i] = graph.subgraph(districts_nodes[i])
        nx.set_node_attributes(districts[i], random_hex(), 'color')
                
    return districts
divided_graph = divide_graph(new_graph, 4, 20)
#%%
def main(no_districts, max_xy):
    short_graph = new_graph
    districts = divided_graph
    draw_graph(short_graph, 1)

main(4, 20)