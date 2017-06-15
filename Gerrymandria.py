#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:49:39 2017

@author: bribartz
"""

from shapely.geometry import Polygon
from shapely.ops import cascaded_union
import random

class CBlock:
    def __init__(self, dems, reps, population, shape):
        self.dems = dems 
        self.reps = reps 
        self.population = 100
        self.shape = shape

   

class District:
    def __init__(self, name, cblocks):
        self.name = name
        self.cblocks = cblocks
        self.shape = cascaded_union([cblock.shape for cblock in cblocks])

class State:
    def __init__(self, districts, all_cblocks):
        self.districts = districts
        self.all_cblocks = all_cblocks
        

cblock_array = []
for i in range(8):
    row = []
    for j in range(8):
        dems = 101
        while dems < 0 or dems > 100:         
            dems = random.gauss(50, 10) 
            reps = 100 - dems
            shape = Polygon([(i,j), (i+1,j), (i+1,j+1), (i,j+1)])
            row.append(CBlock(dems, reps, 100, shape))
    cblock_array.append(row)
#print (cblock_array[0][3].shape.bounds)


def make_dist(min_i, max_i, min_j, max_j, name):
    cblock_set = set()
    for i in range(min_i, max_i):
        for j in range(min_j, max_j):
            cblock_set.add(cblock_array[i][j])
    district = District(name, cblock_set)
    return district

district = make_dist(0,4,0,4, "District 1")
print(district.shape.centroid)
for cblock in district.cblocks:
    print(cblock.dems)


                
        

        

