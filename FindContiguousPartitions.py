#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 25 10:37:26 2018

@author: McKenzie Lamb
"""

import networkx as nx
import random
import warnings

def FindContiguousPartitions(G, numparts = 2, partition_list = [], subgraph = []):
    if subgraph == list(G.nodes()) or numparts == 0:
        return
    
    print('rand_node = ', rand_node)
    #print(G.nodes())
    
#Suppress annoying warnings from matplotlib about deprecated plotting calls 
#from networkx.
def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    fxn()
    
    #Create graph: mxm grid
    m = 2
    G = nx.grid_2d_graph(m, m, periodic=False, create_using=None)
    pos = nx.spectral_layout(G)
    nx.draw(G, pos=pos)
    rand_node = random.choice(list(G.nodes()))    
    FindContiguousPartitions(G, numparts = 2, subgraph = [rand_node])