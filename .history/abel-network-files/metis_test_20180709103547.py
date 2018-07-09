#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 14:06:35 2018

@author: lambm
"""

import networkx as nx
import metis
import random

def MakeGraph():
    H = nx.connected_watts_strogatz_graph(n=50, k=4, p=0.1) 
    G = nx.convert_node_labels_to_integers(H)
    for node in G.nodes():            
        #Generate a random (positive) population for each node.
        G.nodes[node]['pop'] = random.randint(0, 100) 
    return G

#G = metis.example_networkx()
num_parts = 4
G = MakeGraph()
G.graph['node_weight_attr'] = ['pop']

H = metis.networkx_to_metis(G)
(edgecuts, parts) = metis.part_graph(H, num_parts, contig = True)
colors = ['red','blue','green', 'gray']
for i, p in enumerate(parts):
    G.node[i]['color'] = colors[p]
#nx.write_dot(G, 'example.dot') # Requires pydot or pygraphviz
pos = nx.kamada_kawai_layout(G)
labels = {n: str(G.node[n]['pop']) for n in G.nodes()}
nx.draw(G, with_labels=False, node_color = [G.node[i]['color'] for i in G.nodes()],  pos = pos)
nx.draw_networkx_labels(G,pos,labels,font_size=12,font_color='black') 
dist_pops = {p: 0 for p in parts}
for i, p in enumerate(parts):
    dist_pops[p] += G.node[i]['pop']
print("Parity = ", sum([G.node[i]['pop'] for i in G.nodes()])/num_parts)
print("District Populations: ", list(dist_pops.values()))
