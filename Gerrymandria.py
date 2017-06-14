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
        self.dems = dems # min(100, max(0, random.gauss(50, 20)))
        self.reps = reps #100 - self.dems
        self.population = 100
        self.shape = shape
        

class District(object):
    def __init__(self, name, cblocks, shape):
        self.name = name
        self.cblocks = cblocks
        self.shape = shape

class State(object):
    def __init__(self, districts, all_cblocks):
        self.districts = districts
        self.all_cblocks = all_cblocks
        

#cblock_1 = CBlock(dems, reps, Polygon([(0,0),(1,0),(1,1),(0,1)]))
#cblock_2 = CBlock(dems, reps, Polygon([(1,0),(1,1),(2,1),(2,0)]))
#print (cblock_1.dems)
#print (cblock_1.reps)
#print (cblock_2.dems)
#print (cblock_2.reps)
#district_1 = District('A', [cblock_1, cblock_2], cblock_1.shape.union(cblock_2.shape))
#print (district_1.shape.area)
c_block_array = []
for i in range(32):
    row = []
    for j in range(32):
        dems = 101
        while dems < 0 or dems > 100:         
            dems = random.gauss(50, 10) 
            reps = 100 - dems
            row.append(CBlock(dems, reps, 100, True))
    c_block_array.append(row)

for i in range(3):
    print([c_block_array[i][j].dems for j in range(3)])
        

        

