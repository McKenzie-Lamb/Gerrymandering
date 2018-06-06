#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 25 10:37:26 2018

@author: McKenzie Lamb
"""

import networkx as nx
import random
import warnings
from copy import deepcopy
from tabulate import tabulate
import time  # Timer function
from multiprocessing import Pool
import cProfile
import itertools
import math

# Timer code.
timeList = []

def timer():
    timeList.append(time.time())
    if len(timeList) % 2 == 0:
        print('Time elapsed: ' + str(round(timeList[-1] - timeList[-2], 4)) + ' seconds.')
        timeList.pop()
        timeList.pop()




#Finds all partitions into 2 connected subsets by first enumerating all 
#partitions and then checking for connectedness.  Surely this will not scale well.
def BruteForcePartitioner(G):
    node_list = G.nodes()
    n = len(node_list)
    partition_set = set() #Use a set to prevent duplicates.
#    s_list = []
    for i in range(1, math.floor(n/2)+1):
        subsets = itertools.combinations(node_list, i)
        for s in subsets:
            comp_nodes = [node for node in node_list if node not in s]
            subgraph = G.subgraph(s)
            comp_subgraph = G.subgraph(comp_nodes)
            if nx.is_connected(subgraph) and nx.is_connected(comp_subgraph):
                    
                #Sort each component to avoid double counting different 
                #node orders.
                parts = [sorted(list(s)), sorted(comp_nodes)]  
                
                #Sort components by minimum element to avoid double counting 
                #different component orders. Since components are disjoint,
                #we can use the minimum element from each (they will be distinct).
                parts.sort(key=lambda x: min(x)) 
                
                #Retype as tuples (hashable) and add to set.
                partition_set.add((tuple(parts[0]), tuple(parts[1])))                
    return partition_set

#Use multiple processes in parallel.  Not working yet.                  
def BruteForceParallel(G):
    node_list = G.nodes()
    n = len(node_list)
    partition_set = set() #Use a set to prevent duplicates.
#    s_list = []
    subsets = []
    for i in range(1, math.floor(n/2)+1):
        subsets += itertools.combinations(node_list, i)
    for s in subsets:
        comp_nodes = [node for node in node_list if node not in s]
        subgraph = G.subgraph(s)
        comp_subgraph = G.subgraph(comp_nodes)
        if nx.is_connected(subgraph) and nx.is_connected(comp_subgraph):
                
            #Sort each component to avoid double counting different 
            #node orders.
            parts = [sorted(list(s)), sorted(comp_nodes)]  
            
            #Sort components by minimum element to avoid double counting 
            #different component orders. Since components are disjoint,
            #we can use the minimum element from each (they will be distinct).
            parts.sort(key=lambda x: min(x)) 
            
            #Retype as tuples (hashable) and add to set.
            partition_set.add((tuple(parts[0]), tuple(parts[1])))                
    return partition_set        
        
#Anton's binary recursion tree algorithm.  
#For each node, choose both to include it and to exclude it from a subset that
#forms one piece of a partition. 
#Only implemented for partitions into 2 pieces so far.
def BinaryPartitioner(G, node_labels, partition_set = set()):
#   For debugging.
#    print('--------------------------------')
#    print('yes: ', node_labels['y'])
#    print('no: ', node_labels['n'])
#    print('undecided: ', node_labels['u'])
#    input('Continue?')
    

    #Terminal condition: no undecided nodes remain.
    if node_labels['u'] == []:
#        print('End of Branch')
        
        #Check that yes and no components are connected and non-empty.  
        #If so, add to partion_set.
        if not node_labels['y'] == [] and not node_labels['n'] == []:
            if nx.is_connected(G.subgraph(node_labels['n'])):
    
                #Sort each component to ensure uniqueness.  Maybe not needed.
                parts = [sorted(node_labels['y']), sorted(node_labels['n'])]
                
                #Sort components to avoid repeats.
                parts.sort(key=lambda x: min(x))
                partition_set.add((tuple(parts[0]), tuple(parts[1])))
        return
    elif node_labels['y'] == []:
        new_node_labels = deepcopy(node_labels)
        min_u_node = min(new_node_labels['u'])
        
        #About to make choices, so will no longer be undecided.
        new_node_labels['u'].remove(min_u_node)

        #Make choice 'yes'.
        new_node_labels['y'].append(min_u_node)
        BinaryPartitioner(G, new_node_labels, partition_set)
        
        #Make choice 'no'.
        new_node_labels['y'].remove(min_u_node)        
        new_node_labels['n'].append(min_u_node)
        BinaryPartitioner(G, new_node_labels, partition_set)
              
    else:
        new_node_labels = deepcopy(node_labels)
        yes_subgraph = G.subgraph(new_node_labels['y'])
        y_boundary = nx.node_boundary(G, yes_subgraph)
        uy_boundary = [bn for bn in y_boundary if bn in new_node_labels['u']]

        #If no undecided boundary nodes, mark all undecided nodes as 'no'.
        if uy_boundary == []:
#            print('***No undecided boundary***')
            u_nodes = node_labels['u']
            for node in u_nodes:
                new_node_labels['u'].remove(node)
                new_node_labels['n'].append(node)
            BinaryPartitioner(G, new_node_labels, partition_set)        

                
        #If there are undecided boundary nodes, choose the minimum.
        else:
            min_u_node = min(uy_boundary)
            
            #About to make choices, so will no longer be undecided.
            new_node_labels['u'].remove(min_u_node)
    
            #Make choice 'yes'.
            new_node_labels['y'].append(min_u_node)
            BinaryPartitioner(G, new_node_labels, partition_set)
            
            #Make choice 'no'.
            new_node_labels['y'].remove(min_u_node)        
            new_node_labels['n'].append(min_u_node)
            BinaryPartitioner(G, new_node_labels, partition_set)        



#Suppress annoying warnings from matplotlib about deprecated plotting calls 
#from networkx.
def fxn():
    warnings.warn("deprecated", DeprecationWarning)

def RunBruteForcePartitioner():
    with warnings.catch_warnings():
        G = nx.convert_node_labels_to_integers(nx.grid_2d_graph(4, 3, periodic=False, create_using=None))
        pos = nx.spectral_layout(G)
        timer()
        partition_set = BruteForcePartitioner(G)
        timer()
    #    for part in partition_set:
    #        print(part[0], '-----', part[1])
#        print(tabulate(list(partition_set)))
        print('Number of Connected Partitions = ', len(partition_set))
        return partition_set
#        warnings.simplefilter("ignore")
#        fxn()
#        nx.draw(G, with_labels=True, pos=pos)
#        example = partition_set.pop()
#        part1_nodes = list(example[0])
#        part2_nodes = list(example[1])
#        part1_subgraph = G.subgraph(part1_nodes)
#        part2_subgraph = G.subgraph(part2_nodes)
#        nx.draw(part1_subgraph, with_labels=True, pos=pos, node_color='b')
#        nx.draw(part2_subgraph, with_labels=True, pos=pos, node_color='g')
        
def RunBinaryPartitioner():
    with warnings.catch_warnings():
        G = nx.convert_node_labels_to_integers(nx.grid_2d_graph(4, 3, periodic=False, create_using=None))
        node_labels = {'u': list(G.nodes()), 'y': [], 'n': []}
        timer()
        partition_set = set()
        BinaryPartitioner(G, node_labels, partition_set)
        timer()
    #    for part in partition_set:
    #        print(part[0], '-----', part[1])
#        print(tabulate(list(partition_set)))
        print('Number of Connected Partitions = ', len(partition_set))
        
        
        warnings.simplefilter("ignore")
        fxn()
        pos = nx.spectral_layout(G)
        nx.draw(G, with_labels=True, pos=pos)
#        example = partition_set.pop()
#        part1_nodes = list(example[0])
#        part2_nodes = list(example[1])
#        part1_subgraph = G.subgraph(part1_nodes)
#        part2_subgraph = G.subgraph(part2_nodes)
#        nx.draw(part1_subgraph, with_labels=True, pos=pos, node_color='b')
#        nx.draw(part2_subgraph, with_labels=True, pos=pos, node_color='g')
        return partition_set

#Compare results from two different algorithms.
#set1 = RunBinaryPartitioner()
#set2 = RunBruteForcePartitioner()
#diff = set2 - set1
#print(tabulate(list(diff)))  

RunBinaryPartitioner()