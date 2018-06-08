#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 25 10:37:26 2018

@author: McKenzie Lamb
"""

import networkx as nx
import random
import warnings
from copy import deepcopy, copy
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
    parity = G.graph['parity']
    margin = G.graph['margin']
    n = len(node_list)
    partition_set = set() #Use a set to prevent duplicates.
#    s_list = []
    for i in range(1, math.floor(n/2)+1): #Only need half.
        subsets = itertools.combinations(node_list, i)
        for s in subsets:
            comp_nodes = [node for node in node_list if node not in s]
            subgraph = G.subgraph(s)
            comp_subgraph = G.subgraph(comp_nodes)
            total_pop_yes = sum([G.nodes[node]['pop'] for node in s])
            total_pop_no = sum([G.nodes[node]['pop'] for node in comp_nodes])
            
            #Check that pop for each component is within margin.
            if abs(total_pop_yes - parity) < margin and abs(total_pop_no - parity) < margin:
                
                #Check that each component is connected.
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
def BinaryPartitioner(G, node_labels, partition_set):
    #Add up # of dems in current partition component.
    total_pop_yes = sum([G.nodes[node]['pop'] for node in G.nodes() if node in node_labels['y']])
    total_pop_no = sum([G.nodes[node]['pop'] for node in G.nodes() if node in node_labels['n']])
    
#   For debugging.
#    print('--------------------------------')
#    print('yes: ', node_labels['y'])
#    print('no: ', node_labels['n'])
#    print('undecided: ', node_labels['u'])
#    print('parity: ', parity)
#    print('total_pop_yes: ', total_pop_yes)
#    input('Continue?')

    
    #Prune branch (bail) if we have exceeded population parity threshold 
    #in either yes or no component.
    if (total_pop_yes > G.graph['parity'] + G.graph['margin'] 
    or total_pop_no > G.graph['parity'] + G.graph['margin']):
        return
        
    #Terminal condition: no undecided nodes remain.
    if node_labels['u'] == []:
#        print('End of Branch')
        
        #Check that yes and no components are non-empty.  
        if node_labels['y'] == [] or node_labels['n'] == []:
            return
         
        #Check that populations are both close enough to parity.
        total_pop_no = sum([G.nodes[node]['pop'] for node in G.nodes() if node in node_labels['n']])
        if (total_pop_yes < G.graph['parity'] - G.graph['margin'] 
        or total_pop_no < G.graph['parity'] - G.graph['margin']):
            return
        
        #Check connectedness of other component.
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

#Node class for rectangular grid-specific partitioner.
class GNode:
    def __init__(self, coords, number, label):
        self.coords = coords
        self.number = number
        self.label = label

#Checks connectedness on a grid.  
#Not working yet. (Currently checks a necessary but not sufficient condition.)
def IsConnected(nodes):
    x_coords = {n.coords[0] for n in nodes}
    y_coords = {n.coords[1] for n in nodes}
    x_min = min(x_coords)
    x_max = max(x_coords)
    y_min = min(y_coords)
    y_max = max(y_coords)
    x_connected = bool(x_coords == set(range(x_min, x_max + 1)))
    y_connected = bool(y_coords == set(range(y_min, y_max + 1)))
    return x_connected and y_connected

def UYBoundary(nodes, yes, undecided):
    boundary = set()
    y_coords = {n.coords for n in yes}
    for u_node in undecided:
        if ((u_node.coords[0]+1, u_node.coords[1]) in y_coords or
            (u_node.coords[0]-1, u_node.coords[1]) in y_coords or
            (u_node.coords[0], u_node.coords[1]+1) in y_coords or
            (u_node.coords[0], u_node.coords[1]-1) in y_coords):
            boundary.add(u_node)
    return boundary

    
#Variation on Anton's binary recursion tree algorithm.  
#Optimized for (and only works for) rectangular grids.
#Not working yet.
def BinaryPartitionerGrid(nodes, partition_set = set()):
    undecided = [n for n in nodes if n.label == 'u']
    yes = [n for n in nodes if n.label == 'y']
    no = [n for n in nodes if n.label == 'n']
    
    
#   For debugging.
    print('--------------------------------')
    print('yes: ', [n.number for n in yes])
    print('no: ', [n.number for n in no])
    print('undecided: ', [n.number for n in undecided])
#    input('Continue?')
    

    #Terminal condition: no undecided nodes remain.
    if undecided == []:
#        print('End of Branch')
        
        #Check that yes and no components are connected and non-empty.  
        #If so, add to partion_set.
        if not yes == [] and not no == []:
            if IsConnected(no):
    
                #Sort each component to ensure uniqueness.  Maybe not needed.
                parts = [sorted([n.number for n in yes]), sorted([n.number for n in no])]
                
                #Sort components to avoid repeats.
                parts.sort(key=lambda x: min(x))
                partition_set.add((tuple(parts[0]), tuple(parts[1])))
        return
    elif yes == []:
        new_nodes = copy(nodes)
        min_u_node = min(undecided, key=lambda n: n.number)

        #Make choice 'yes'.
        min_u_node.label = 'y'
        BinaryPartitionerGrid(new_nodes, partition_set)
        
        #Make choice 'no'.
        min_u_node.label = 'n'        
        BinaryPartitionerGrid(new_nodes, partition_set)
        
        #Change back to undecided.
        min_u_node.label = 'u' 
    else:
        new_nodes = copy(nodes)
        uy_boundary = UYBoundary(new_nodes, yes, undecided)
        
        #If no undecided boundary nodes, mark all undecided nodes as 'no'.
        if len(uy_boundary) == 0:
#            print('***No undecided boundary***')
            for node in undecided:
                node.label = 'n'
            BinaryPartitionerGrid(new_nodes, partition_set)        

                
        #If there are undecided boundary nodes, choose the minimum.
        else:
            min_u_node = min(uy_boundary, key=lambda n: n.number)
    
            #Make choice 'yes'.
            min_u_node.label = 'y'
            BinaryPartitionerGrid(new_nodes, partition_set)
            
            #Make choice 'no'.
            min_u_node.label = 'n'        
            BinaryPartitionerGrid(new_nodes, partition_set)

            #Change back to undecided.
            min_u_node.label = 'u' 

#******************Testing Code***************************

#Suppress annoying warnings from matplotlib about deprecated plotting calls 
#from networkx.
def fxn():
    warnings.warn("deprecated", DeprecationWarning)

def MakeGraph(m=3, n=3, margin_percentage = 0.2):
    G = nx.convert_node_labels_to_integers(nx.grid_2d_graph(m, n, periodic=False, create_using=None))
    for node in G.nodes():            
        G.nodes[node]['pop'] = random.gauss(50, 10)

    #Calculate demographics
    G.graph['margin_percentage'] = margin_percentage
    G.graph['total_pop'] = sum([G.nodes[node]['pop'] for node in G.nodes()])
    G.graph['parity'] = G.graph['total_pop'] / 2
    G.graph['margin'] = G.graph['parity'] * G.graph['margin_percentage']
    return G
    
def DisplaySamplePartition(G, partition_set):
    with warnings.catch_warnings():
        example = partition_set.pop()
        part1_nodes = list(example[0])
        part2_nodes = list(example[1])
        part1_subgraph = G.subgraph(part1_nodes)
        part2_subgraph = G.subgraph(part2_nodes)
        pos = nx.spectral_layout(G)
        nx.draw(G, with_labels=True, pos=pos)
        nx.draw(part1_subgraph, with_labels=True, pos=pos, node_color='b')
        nx.draw(part2_subgraph, with_labels=True, pos=pos, node_color='g')

def PrintResults(G, partition_set, print_list=False):
    with warnings.catch_warnings():
        if print_list == True:
            print(tabulate(list(partition_set)))
        print('Number of Connected Partitions = ', len(partition_set))
        warnings.simplefilter("ignore")
        fxn()
        pos = nx.spectral_layout(G)
        nx.draw(G, with_labels=True, pos=pos)


def RunBruteForcePartitioner(m=3, n=3, margin_percentage = 0.2):
    G = MakeGraph(m,n, margin_percentage)
    timer()
    partition_set = BruteForcePartitioner(G)
    timer()
    return G, partition_set

        
def RunBinaryPartitioner(m=3, n=3, margin_percentage = 0.2):
    G = MakeGraph(m,n, margin_percentage)            
    #All nodes start out undecided.
    node_labels = {'u': list(G.nodes()), 'y': [], 'n': []}

    timer() #Start timer.
    partition_set = set()
    BinaryPartitioner(G, node_labels, partition_set)
    timer() #Stop timer.
    return G, partition_set



#def RunBinaryPartitionerGrid(m=3, n=3):
#    G = nx.grid_2d_graph(m, n, periodic=False, create_using=None)
#    nodes = [GNode(coords, 0, 'u') for coords in list(G.nodes())]
#    for i in range(len(nodes)):
#        nodes[i].number = i
#    timer()
#    partition_set = set()
#    BinaryPartitionerGrid(nodes, partition_set)
#    timer()
#    return G, partition_set
    

#Compare results from binary and brute force algorithms.
def CompareBinaryBrute(m=3, n=3, margin_percentage = 1):
    G = MakeGraph(m,n, margin_percentage)

    #All nodes start out undecided.
    node_labels = {'u': list(G.nodes()), 'y': [], 'n': []}
    
    binary_partition_set = set()
    BinaryPartitioner(G, node_labels, binary_partition_set)
    PrintResults(G, binary_partition_set, print_list=False)
    
    
    brute_partition_set = BruteForcePartitioner(G)
#    print(tabulate(list(binary_partition_set)))
    
    diff = brute_partition_set - binary_partition_set
    if len(diff) != 0:
        print('Differences Found:')
        print(tabulate(list(diff)))
    else:
        print('Identical results.')


G, partition_set = RunBruteForcePartitioner(m=5, n=5, margin_percentage = 0.01)
#PrintResults(G, partition_set)

#CompareBinaryBrute()