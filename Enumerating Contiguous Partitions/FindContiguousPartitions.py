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

#Enumerates all partitions of set ns into m parts.
#Code from Stack Exchange based on Knuth's book.
def general_partitioner(ns, m):
    def visit(n, a):
        ps = [[] for i in range(m)]
        for j in range(n):
            ps[a[j + 1]].append(ns[j])
        return ps

    def f(mu, nu, sigma, n, a):
        if mu == 2:
            yield visit(n, a)
        else:
            for v in f(mu - 1, nu - 1, (mu + sigma) % 2, n, a):
                yield v
        if nu == mu + 1:
            a[mu] = mu - 1
            yield visit(n, a)
            while a[nu] > 0:
                a[nu] = a[nu] - 1
                yield visit(n, a)
        elif nu > mu + 1:
            if (mu + sigma) % 2 == 1:
                a[nu - 1] = mu - 1
            else:
                a[mu] = mu - 1
            if (a[nu] + sigma) % 2 == 1:
                for v in b(mu, nu - 1, 0, n, a):
                    yield v
            else:
                for v in f(mu, nu - 1, 0, n, a):
                    yield v
            while a[nu] > 0:
                a[nu] = a[nu] - 1
                if (a[nu] + sigma) % 2 == 1:
                    for v in b(mu, nu - 1, 0, n, a):
                        yield v
                else:
                    for v in f(mu, nu - 1, 0, n, a):
                        yield v

    def b(mu, nu, sigma, n, a):
        if nu == mu + 1:
            while a[nu] < mu - 1:
                yield visit(n, a)
                a[nu] = a[nu] + 1
            yield visit(n, a)
            a[mu] = 0
        elif nu > mu + 1:
            if (a[nu] + sigma) % 2 == 1:
                for v in f(mu, nu - 1, 0, n, a):
                    yield v
            else:
                for v in b(mu, nu - 1, 0, n, a):
                    yield v
            while a[nu] < mu - 1:
                a[nu] = a[nu] + 1
                if (a[nu] + sigma) % 2 == 1:
                    for v in f(mu, nu - 1, 0, n, a):
                        yield v
                else:
                    for v in b(mu, nu - 1, 0, n, a):
                        yield v
            if (mu + sigma) % 2 == 1:
                a[nu - 1] = 0
            else:
                a[mu] = 0
        if mu == 2:
            yield visit(n, a)
        else:
            for v in b(mu - 1, nu - 1, (mu + sigma) % 2, n, a):
                yield v

    n = len(ns)
    a = [0] * (n + 1)
    for j in range(1, m + 1):
        a[n - m + j] = j - 1
    return f(m, n, 0, n, a)


#Finds all partitions into m connected subsets by first enumerating all 
#partitions and then checking for connectedness.  Surely this will not scale well.
def BruteForcePartitioner(G, num_parts):
    node_list = list(G.nodes())
    partition_set = set() #Use a set to prevent duplicates.
    all_partitions = general_partitioner(node_list, num_parts)
    for p in all_partitions:
        
            #Check that each component is connected and that 
            #populations are close enough to parity.
            if IsValid(G, p):
            
                #Sort each component to avoid double counting different 
                #node orders.
                parts = [sorted(s) for s in p]  
                
                #Sort components by minimum element to avoid double counting 
                #different component orders. Since components are disjoint,
                #we can use the minimum element from each (they will be distinct).
                parts.sort(key=lambda x: min(x)) 
                
                #Retype as tuples (hashable) and add to set.
                partition_set.add((tuple(part) for part in parts))                
    return partition_set


def IsValid(G, p):
    return ParityCheck(G, p) and IsConnected(G, p)

def IsValidTuple(t):
    p = t[0]
    G = t[1]
    return ParityCheck(G, p) and IsConnected(G, p)


def ParityCheck(G, p):
    parity = True
    for s in p:
        total_pop = sum([G.nodes[node]['pop'] for node in s])
        if abs(total_pop - G.graph['parity']) > G.graph['margin']:
            parity = False
            break 
    return parity

#def ParityCheck(G, p):
#    total_pops = [sum([G.nodes[node]['pop'] for node in s]) for s in p]
#    pop_checks = [bool(abs(pop - G.graph['parity']) < G.graph['margin']) for pop in total_pops]  
#    return False not in pop_checks


def IsConnected(G, p):
    connected = True
    for s in p:
        sg = G.subgraph(s)
        if not nx.is_connected(sg):
            connected = False
            break  
    return connected
        

#Use multiple processes in parallel.                 
def BruteForceParallel(G, num_parts = 2):
    node_list = list(G.nodes())
    partition_set = set() #Use a set to prevent duplicates.
    all_partitions = general_partitioner(node_list, num_parts)
    aps_w_graph = [(p, G) for p in all_partitions] 
    pool = Pool()
    valid_list = pool.map(IsValidTuple, aps_w_graph)
    for i in range(len(aps_w_graph)):
            #Check that each component is connected and that 
            #populations are close enough to parity.
            if valid_list[i]:
                p = aps_w_graph[i][0]
                #Sort each component to avoid double counting different 
                #node orders.
                parts = [sorted(s) for s in p]  
                
                #Sort components by minimum element to avoid double counting 
                #different component orders. Since components are disjoint,
                #we can use the minimum element from each (they will be distinct).
                parts.sort(key=lambda x: min(x)) 
                
                #Retype as tuples (hashable) and add to set.
                partition_set.add((tuple(part) for part in parts))                
    return partition_set
        


#Anton's binary recursion tree algorithm.  
#For each node, choose both to include it and to exclude it from a subset that
#forms one piece of a partition. 
#Only implemented for partitions into 2 pieces so far.
def BinaryPartitioner(G, node_labels, partition_set, ncc = True):
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
        
        #Check connectedness of other component (if required).
        if ncc == False or nx.is_connected(G.subgraph(node_labels['n'])):

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
        BinaryPartitioner(G, new_node_labels, partition_set, ncc)
        
        #Make choice 'no'.
        new_node_labels['y'].remove(min_u_node)        
        new_node_labels['n'].append(min_u_node)
        BinaryPartitioner(G, new_node_labels, partition_set, ncc)
              
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
            BinaryPartitioner(G, new_node_labels, partition_set, ncc)        

                
        #If there are undecided boundary nodes, choose the minimum.
        else:
            min_u_node = min(uy_boundary)
            
            #About to make choices, so will no longer be undecided.
            new_node_labels['u'].remove(min_u_node)
    
            #Make choice 'yes'.
            new_node_labels['y'].append(min_u_node)
            BinaryPartitioner(G, new_node_labels, partition_set, ncc)
            
            #Make choice 'no'.
            new_node_labels['y'].remove(min_u_node)        
            new_node_labels['n'].append(min_u_node)
            BinaryPartitioner(G, new_node_labels, partition_set, ncc)        

#General partitioner.
#For partitions into arbitrarily many pieces.
def Partitioner(G, node_labels, num_pieces):
    partition_set = set()
    current_partition = [list(G.nodes())]
    for piece in current_partition:
        pieces = nx.connected_components(G)
        BinaryPartitioner(G, node_labels, num_pieces, current_partition)
    return partition_set

#******************Testing Code***************************

#Suppress annoying warnings from matplotlib about deprecated plotting calls 
#from networkx.
def fxn():
    warnings.warn("deprecated", DeprecationWarning)

def MakeGraph(m=3, n=3):
    G = nx.convert_node_labels_to_integers(nx.grid_2d_graph(m, n, periodic=False, create_using=None))
    for node in G.nodes():            
        #Generate a random (positive) population for each node.
        G.nodes[node]['pop'] = random.randint(0, 100) 
    return G

def CalculateMargin(G, margin_percentage = 0.2, num_parts = 2):
    #Calculate demographics
    G.graph['margin_percentage'] = margin_percentage
    G.graph['total_pop'] = sum([G.nodes[node]['pop'] for node in G.nodes()])
    G.graph['parity'] = G.graph['total_pop'] / 2
    G.graph['margin'] = G.graph['parity'] * G.graph['margin_percentage']
    
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


def RunBruteForcePartitioner(m=3, n=3, margin_percentage = 0.2, num_parts = 2):
    G = MakeGraph(m,n)
    CalculateMargin(G, margin_percentage, num_parts)
    timer()
    partition_set = BruteForcePartitioner(G, num_parts)
    timer()
    PrintResults(G, partition_set)
    return G, partition_set

def RunBruteForceParallel(m=3, n=3, margin_percentage = 0.2, num_parts = 2):
    G = MakeGraph(m,n, margin_percentage)
    CalculateMargin(G, margin_percentage, num_parts)
    timer()
    partition_set = BruteForceParallel(G, num_parts)
    timer()
    return G, partition_set

        
def RunBinaryPartitioner(m=3, n=3, margin_percentage = 0.2):
    G = MakeGraph(m,n) 
    CalculateMargin(G, margin_percentage, 2)
           
    #All nodes start out undecided.
    node_labels = {'u': list(G.nodes()), 'y': [], 'n': []}

    timer() #Start timer.
    partition_set = set()
    BinaryPartitioner(G, node_labels, partition_set, ncc = False)
    timer() #Stop timer.
    return G, partition_set

def RunPartitioner(m=3, n=3, margin_percentage = 0.2, num_parts = 2):
    G = MakeGraph(m,n)
    CalculateMargin(G, margin_percentage, num_parts)            
    node_labels = {'u': list(G.nodes())}
    for i in range(len(num_parts)):
        node_labels[str(i)] = []
    timer() #Start timer.
    partition_set = Partitioner(G, node_labels, partition_set, num_parts = 2)
    timer() #Stop timer.
    return G

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
    G = MakeGraph(m,n)

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

if __name__ == '__main__':
    G, partition_set = RunBruteForcePartitioner(m=3, n=3, margin_percentage = 100, num_parts = 2)
    PrintResults(G, partition_set, print_list=False)
#    DisplaySamplePartition(G, partition_set)
    



#G = nx.convert_node_labels_to_integers(nx.grid_2d_graph(2, 2, periodic=False, create_using=None))
#partitions = general_partitioner(list(G.nodes()), 3)
#for x in partitions:
#    print(x)

#CompareBinaryBrute()