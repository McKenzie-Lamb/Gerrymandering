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
for i in range(32):
    row = []
    for j in range(32):
        dems = 101
        while dems < 0 or dems > 100:         
            dems = random.gauss(50, 10) 
            reps = 100 - dems
            shape = Polygon([(i,j), (i+1,j), (i+1,j+1), (i,j+1)])
            row.append(CBlock(dems, reps, 100, shape))
    c_block_array.append(row)

for i in range(3):
    print([c_block_array[i][j].dems for j in range(3)])
    
district_set = {}
for i in range(32):
    if i%4 == 0:
        for j in range(32):
            if j%4 == 0:
                shape = Polygon([(i,j), (i+4,j), (i+4,j+4), (i,j+4)])
                name = 'name'
                cblocks = {}
                district_set.add
                
        

        

