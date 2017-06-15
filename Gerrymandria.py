#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:49:39 2017

@author: bribartz
"""

from shapely.geometry import Polygon
import random

class CBlock(object):
    def __init__(self, dems, reps, population, shape):
        self.dems = dems 
        self.reps = reps 
        self.population = 100
        self.shape = shape
    def __iter__(self):
        return iter(self.shape.bounds)
   

class District(object):
    def __init__(self, name, cblocks, shape):
        self.name = name
        self.cblocks = cblocks
        self.shape = shape

class State(object):
    def __init__(self, districts, all_cblocks):
        self.districts = districts
        self.all_cblocks = all_cblocks
        

c_block_array = []
for i in range(8):
    row = []
    for j in range(8):
        dems = 101
        while dems < 0 or dems > 100:         
            dems = random.gauss(50, 10) 
            reps = 100 - dems
            shape = Polygon([(i,j), (i+1,j), (i+1,j+1), (i,j+1)])
            row.append(CBlock(dems, reps, 100, shape))
    c_block_array.append(row)
print (c_block_array[0][3].shape.bounds)


def make_dist(min_i, max_i, min_j, max_j):
    cblock_set = {}
    for i in range(min_i, max_i):
        for j in range(min_j, max_j):
            for cblock in c_block_array:
                for coordinates in cblock[3]:
                    if min_i <= coordinates[0] and max_i >= coordinates[0] and min_j <= coordinates[1] and max_j >= coordinates[1]:
                        cblock_set.add(cblock)
    print (cblock_set)

make_dist(0,4,0,4)


                
        

        

