#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 14:06:35 2018

@author: lambm
"""

import networkx as nx
import metis
import random
import pickle
import math
from scipy.stats import truncnorm
import numpy as np
import math
import os

def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
    return truncnorm((low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)

def MakeNXGraphFile(filename = 'small_map3_no_discontiguos.gpickle'):
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    G = nx.read_gpickle(filename)
#    G = nx.convert_node_labels_to_integers(H)
    for n in G.nodes():
        if np.isnan(G.nodes[n]['dem']):
            G.nodes[n]['dem'] = 0
        if np.isnan(G.nodes[n]['rep']):
            G.nodes[n]['rep'] = 0
        G.nodes[n]['tot'] = G.nodes[n]['dem']+G.nodes[n]['rep']
        if G.nodes[n]['tot'] != 0:
            G.nodes[n]['dem_prop'] = int(100*(G.nodes[n]['dem'] / G.nodes[n]['tot']))
        else:
            G.nodes[n]['dem_prop'] = 0
    return G

def MakeNXGraphRand(size = 100, dem_mean = 0.5, dem_sd = 0.3):
    # H = nx.connected_watts_strogatz_graph(n=size, k=8, p=0.1)
    # side_dim = math.floor(math.sqrt(size))
#    H = nx.grid_2d_graph(side_dim, side_dim, periodic=False, create_using=None)
#    H = nx.triangular_lattice_graph(size, size)
    if size == 100:
        multiplier = 165
    elif size == 400:
        multiplier = 370
    elif size == 1000:
        multiplier = 675
    elif size == 10000:
        multiplier =4500
    side_dim = math.floor(math.sqrt(size))
    G = nx.grid_2d_graph(side_dim, side_dim, periodic=False, create_using=None)
#    G = nx.convert_node_labels_to_integers(H)
    pop_generator = get_truncated_normal(mean=100, sd=20, low=0, upp=200)
    max_dfc = (size / 2)**2+(size / 2)**2
    for node in G.nodes():
        #Generate a random (positive) population for each node.
        G.nodes[node]['pop'] = int(round(pop_generator.rvs()))
        dfc = (node[0]-4.5)**2+(node[1]-4.5)**2
        distance_dem_mean = multiplier * (dfc / (max_dfc))
        dem_percent_generator = get_truncated_normal(mean=distance_dem_mean, sd=dem_sd, low=0, upp=1)
        dem_percent = dem_percent_generator.rvs()
        G.nodes[node]['dem'] =int(round(dem_percent * G.nodes[node]['pop']))
    return G

#G = metis.example_networkx()
def MakeGraphPartition(size = 100, num_parts = 4, dem_mean = 0.5, dem_sd = 0.3,
                       filename = 'small_map3_no_discontiguos.gpickle',
                       rand_graph = True, target = [0.25, 0.25, 0.25, 0.25]):
    if rand_graph == True:
        G = MakeNXGraphRand(size, dem_mean = dem_mean, dem_sd = dem_sd)
    else:
        G = MakeNXGraphFile(filename)
    G = nx.convert_node_labels_to_integers(G)
    for n in G.nodes():
        G.nodes[n]['pop']= int(G.nodes[n]['pop'])
    G.graph['node_weight_attr'] = ['dem', 'pop']
    #H = metis.networkx_to_metis(G)
    target = [(t, 1/num_parts) for t in target]
    print("^^^^^Target^^^^^^^^: ", target)
    (edgecuts, parts) = metis.part_graph(G, num_parts, contig = False, ufactor = 100, tpwgts = list(target))
#    colors = ['red','blue','green', 'gray']
#    for i, p in enumerate(parts):
#        G.node[i]['color'] = colors[p]
#    pos = nx.kamada_kawai_layout(G)
#    labels = {n: str(G.node[n]['pop']) for n in G.nodes()}
#    nx.draw(G, with_labels=False, node_color = [G.node[i]['color'] for i in G.nodes()],  pos = pos)
#    nx.draw_networkx_labels(G,pos,labels,font_size=12,font_color='black')
    dist_pops = {p: 0 for p in parts}
    for i, p in enumerate(parts):
        dist_pops[p] += G.node[i]['pop']
    total_pop = sum(dist_pops.values())
    dist_dems = {p: 0 for p in parts}
    for i, p in enumerate(parts):
        dist_dems[p] += G.node[i]['dem']
    total_dem = sum(dist_dems.values())
    print("Parity = ", total_pop / num_parts)
    print("District Populations: ", list(dist_pops.values()))
    print("Pop Percentages: ", [x / total_pop for x in list(dist_pops.values())])
    print("Dem Percentages: ", [x / total_dem for x in list(dist_dems.values())])

#    edgelist = [(a,b) for (a,b,c) in nx.to_edgelist(G)]
    return G, parts

#os.chdir(os.path.dirname(os.path.realpath(__file__)))
##print(os.getcwd())
#G, parts = MakeGraphPartition(size = 10000, num_parts = 8,
#                              filename = 'whole_map_contig_point_adj.gpickle',
#                              rand_graph = False, target = [0.055, 0.135, 0.135, 0.135, 0.135, 0.135, 0.135, 0.135])
#print("Mean Dem Percentage = ", np.mean([G.nodes[n]['dem']/G.nodes[n]['pop'] for n in G.nodes() if G.nodes[n]['pop'] != 0]))
#nx.draw(G, pos=pos)
#nx.draw(part1_subgraph, with_labels=True, pos=pos, node_color='b')
#layout = nx.spectral_layout(G)
#print(layout)
#part_nodes = [list(G)[i] for i in range(len(parts)) if parts[i] == 1]
##print(part_nodes)
#bd = nx.node_boundary(G, part_nodes)
#print(bd)
