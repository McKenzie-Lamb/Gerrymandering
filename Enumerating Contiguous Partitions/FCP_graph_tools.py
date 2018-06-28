#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 23 20:44:40 2018

@author: lambm
"""

import numpy as np
import random
#from copy import deepcopy, copy
#from tabulate import tabulate
import time  # Timer function
from multiprocessing import Pool
import sys
sys.path.append('/usr/local/opt/graph-tool/lib/python3.6/site-packages')
import graph_tool.all as gt

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
#Creates a generater.
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
def BruteForcePartitioner(g, num_parts):
    vertices = g.get_vertices()
    partition_set = set() #Use a set to prevent duplicates.
    all_partitions = general_partitioner(vertices, num_parts)
    for p in all_partitions:
        
        #Check that each component is connected and that 
        #populations are close enough to parity.
        if IsValid(g, p):
        
            #Sort each component to avoid double counting different 
            #node orders.
            parts = [sorted(s) for s in p]  
            
            #Sort components by minimum element to avoid double counting 
            #different component orders. Since components are disjoint,
            #we can use the minimum element from each (they will be distinct).
            parts.sort(key=lambda x: min(x)) 
            
            #Retype as tuples (hashable) and add to set.
            partition_set.add(tuple(tuple(part) for part in parts)) 
            
    return partition_set


def IsValid(g, p):
#    return ParityCheck(g, p) and IsConnected(g, p)
    return IsConnected(g, p)

def IsValidTuple(t):
    p = t[0]
    g = t[1]
    return ParityCheck(g, p) and IsConnected(g, p)

def ParityCheck(g, p):
    for s in p:
        total_pop = np.sum(g.vp['pop'].a)
        if abs(total_pop - g.gp['parity']) > g.gp['margin']:
            return False 
    return True

#def ParityCheck(G, p):
#    total_pops = [sum([G.nodes[node]['pop'] for node in s]) for s in p]
#    pop_checks = [bool(abs(pop - G.graph['parity']) < G.graph['margin']) for pop in total_pops]  
#    return False not in pop_checks


def IsConnected(g, p):
#    print("p = ", p)
    for s in p:
        vfilt = g.new_vertex_property('bool');
        for i in s:
            vfilt[i] = True  
        sub = gt.GraphView(g, vfilt)
        comp, hist = gt.label_components(sub, attractors=False)
        if not np.sum(comp.a) == 0:
            return False  
#    DisplayPartition(g, p)
    return True
        
#def IsConnected(g, p):
#    print(p)
#    for s in p:
#        vfilt = g.new_vertex_property('bool');
#        for i in s:
#            vfilt[i] = True  
#        sub = gt.GraphView(g, vfilt)
#        comp, hist = gt.label_components(sub, attractors=True)
#        if not np.sum(comp.a) == 0:
#            return False  
#    return True

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
                partition_set.add(tuple(tuple(part) for part in parts))                
    return partition_set
        

#****************Testing Code*********************

def MakeGraph(m=3, n=3):
    g = gt.lattice([m, n])

    #Generate a random (positive) population for each node.
    g.vp['pop'] = g.new_vertex_property('int')
    g.vp['pop'].a = np.random.randint(0,100, g.num_vertices())
    return g

def DisplayPartition(g, p):
    vfilt = g.new_vertex_property('bool')
    for i in p[0]:
        vfilt[i] = True  
    sub = gt.GraphView(g, vfilt)
    comp, hist = gt.label_components(sub, attractors=True)
    pos = gt.sfdp_layout(g, cooling_step=0.95, epsilon=1e-2)
    gt.graph_draw(sub, pos=pos, vertex_text = g.vertex_index, output_size=(300,300))

def CalculateMargin(g, margin_percentage = 0.2, num_parts = 2):
    #Calculate demographics
    total_pop = np.sum(g.vp['pop'].a)                
    g.gp['parity'] = g.new_graph_property("double")
    g.gp['parity'] =  total_pop / num_parts
    g.gp['margin'] = g.new_graph_property("double")                  
    g.gp['margin'] = g.gp['parity'] * margin_percentage 
    print(g.gp['parity'])
    print(g.gp['margin'])

def RunBruteForcePartitioner(m=3, n=3, margin_percentage = 0.2, num_parts = 2):
    g = MakeGraph(m,n)
    CalculateMargin(g, margin_percentage, num_parts)
    print()
    timer()
    partition_set = BruteForcePartitioner(g, num_parts)
    timer()
    return g, partition_set

def RunBruteForceParallel(m=3, n=3, margin_percentage = 0.2, num_parts = 2):
    G = MakeGraph(m,n, margin_percentage)
    timer()
    partition_set = BruteForceParallel(G, num_parts)
    timer()
    return G, partition_set

#if __name__ == '__main__':
#    g, partition_set = RunBruteForcePartitioner(m=3, n=3, margin_percentage = 1)
#
##    PrintResults(G, partition_set, print_list=False)
##    g = MakeGraph(m=2, n=2)
##    CalculateMargin(g, margin_percentage = 1)
##    partition_list = general_partitioner(g.get_vertices(), 3)
##    for p in partition_set:
##        print(IsValid(g, p))
##    print(IsConnected(g, p))
##    partition_set = BruteForcePartitioner(g, 2)
#    print('Number of Connected Partitions = ', len(partition_set))
##    print(list(partition_set))
#    for p in partition_set:
#        print(p)
#    pos = gt.sfdp_layout(g, cooling_step=0.95, epsilon=1e-2)
#    v_prop = g.new_vertex_property('int')
#    gt.graph_draw(g, pos=pos, vertex_text = g.vertex_index, output_size=(300,300))
    
#    p = [[0,1,4], [2,3,5]]
#    DisplayPartition(g, [p[1], p[0]])
#    print(IsConnected(g, p))
    
#    partition = partition_set.pop()
#    print(partition)
#    DisplayPartition(g, partition)
    
g, partition_set = RunBruteForcePartitioner(m=3, n=3, margin_percentage = 100, num_parts = 2)
print('Number of Connected Partitions = ', len(partition_set))
gt.graph_draw(g, vertex_text = g.vertex_index, output_size=(300,300))
#partition = partition_set.pop()
#print(partition)
#DisplayPartition(g, partition)