#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:49:39 2017

@author: bribartz
"""

from shapely.geometry import Polygon
from shapely.ops import cascaded_union
import random
import collections

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
    def __init__(self, name, districts, all_cblocks):
        self.name = name 
        self.districts = districts
        self.shape = cascaded_union([district.shape for district in districts])
        self.all_cblocks = all_cblocks
        
def make_cblocks():        
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
    return cblock_array


def make_dist(min_i, max_i, min_j, max_j, name, cblock_array):
    cblock_set = set()
    for i in range(min_i, max_i):
        for j in range(min_j, max_j):
            cblock_set.add(cblock_array[i][j])
    district = District(name, cblock_set)
    return district

def make_state(name):
    all_cblocks = make_cblocks()
    district_set = set()
    district_num = 1
    for i in range(0,8,4):
        for j in range(0,8,4):
            district = make_dist (i, i+4, j, j+4, "{0}-{1}".format(name, district_num), all_cblocks)
            district_set.add(district)
            district_num += 1
    state = State(name, district_set, all_cblocks)
    return state 

state_names = "ABCDEFGHIJKLMNOP"
state_set = {make_state(name) for name in state_names}
All_district = []
for state in state_set:
     for district in state.districts:
          All_district.append(district)

New_list = []
for dist in All_district:       #creates new list of districts to make up random 
    if dist.name[:1] != state:  #list of districts that discludes districts from given state   
        New_list.append(dist) 

def demographic_breakdown(state):    #find percentages of Democrats&Republicans in a given state
    dems_list = []
    reps_list = []
    for i in range(len(All_district)):
        if All_district[i].name[:1] == state: #look at only districts in given state
            for cblocks in All_district[i].cblocks:
                dems_list.append(cblocks.dems)    #make list of number of Democrats in state's cblocks
                reps_list.append(cblocks.reps) #make list of number of Republicans in state's cblocks
    total_dem = sum(dems_list)
    total_rep = sum(reps_list)
    total_pop = total_dem + total_rep 
    print (total_dem, total_rep, total_pop)
    total_percent_dem = total_dem / total_pop       #percent of votes cast for Democrat in given state
    total_percent_rep = total_rep / total_pop       #percent of votes cast for Republican in given state                                   
    return total_percent_dem, total_percent_rep

state = input('Insert the abbreviation of the state: ', )
demographic_breakdown(state)
total_percent_dem = demographic_breakdown(state)[0]
total_percent_rep = demographic_breakdown(state)[1]


number_samples = 100

count_dist = collections.Counter([dist.name[:1] for dist in All_district])
number_district = count_dist.get(state)     #number of districts in given state 

#print (state_set.pop().shape.area)
#for state in state_set:
#    print (state.districts.pop().name)
#state_A = make_state("A")
#print(state_A.districts.pop().name)
#district = make_dist(0,4,0,4, "District 1")
#print(district.shape.centroid)
#for cblock in district.cblocks:
#    print(cblock.dems)


#x,y = p.exterior.xy
#plt.plot(x,y,...)

                
        

        

