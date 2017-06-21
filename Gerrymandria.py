#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:49:39 2017

@author: bribartz
"""

from shapely.geometry import Polygon
from shapely.geometry import Point
from shapely.ops import cascaded_union
import matplotlib.pyplot as plt
from descartes.patch import PolygonPatch
import random
import collections

def is_adjacent(shape1, shape2):
        return (shape1 is not shape2 and shape1.touches(shape2) 
                 and not isinstance(shape1.intersection(shape2),Point))


class CBlock:
    def __init__(self, dems, reps, population, shape):
        self.dems = dems 
        self.reps = reps 
        self.population = population
        self.shape = shape
        self.state = None
        self.district = None
        
    def __str__(self):
        return "({0}-{1})".format(self.dems,self.reps)
        
    def plot_block(self, plot):
        dem_share = self.dems/(self.dems+self.reps)
        if dem_share > .5:
            color = 'blue'
            alph = dem_share
        elif dem_share < .5:
            color = 'red'
            alph = (1-dem_share)
        else:
            color = 'magenta'
            alph = 1
        x,y = self.shape.exterior.xy
        plot.plot(x,y,color='none',zorder=1)
        patch = PolygonPatch(self.shape,facecolor=color,edgecolor='none',alpha=alph,zorder=2)
        plot.add_patch(patch)
        
    def is_adjacent(self, other_block):
        return is_adjacent(self.shape,other_block.shape)


class District:
    def __init__(self, name, cblocks):
        self.name = name
        self.cblocks = cblocks
        self.shape = cascaded_union([cblock.shape for cblock in cblocks])
        for cblock in cblocks:
            cblock.district = self
        self.index = None
        
    def __str__(self):
        return self.name
        
    def plot_district(self,plot):
        for block in self.cblocks:
            block.plot_block(plot)
        x,y=self.shape.exterior.xy
        plot.plot(x,y,linestyle='dotted',color='black',lw=2)
        c = self.shape.centroid.coords[0]
        plot.text(c[0],c[1],self)

class State:
    def __init__(self, name, districts, all_cblocks):
        self.name = name 
        self.districts = districts
        self.shape = cascaded_union([district.shape for district in districts])
        self.all_cblocks = all_cblocks
        for cblock in all_cblocks:
            cblock.state = self
        self.adjacent_blocks = []
        index = 0
        for district in districts:
            row = []
            district.index = index
            for other_district in districts:
                adj = self.find_adjacent(district,other_district)[0]
                row.append(adj)
            self.adjacent_blocks.append(row)
            index += 1
            
        
    def __str__(self):
        return self.name
        
    def plot_state(self,plot):
        for district in self.districts:
            district.plot_district(plot)
        x,y = self.shape.exterior.xy
        plot.plot(x,y,color='black',lw=3)
        
    def find_adjacent(self, district1, district2):
        adj_from = set()
        adj_to = set()
        if district1 is not district2:                    
            for block in district1.cblocks:
                for other_block in district2.cblocks:
                    if block.is_adjacent(other_block):
                        adj_from.add(block)
                        adj_to.add(other_block)
        return adj_from,adj_to

    def pairwise_swap(self,district1, district2):
        if (district1 is district2 or not is_adjacent(district1.shape,district2.shape)
            or district1.state is not self or district2.state is not self):
                return False
        #choose a random block in district1 which is adjacent to district2 and vice versa
        adj_blocks1 = self.adjacent_blocks[district1.index][district2.index]
        adj_blocks2 = self.adjacent_blocks[district2.index][district1.index]
        adj1 = random.choice(adj_blocks1)
        adj2 = random.choice(adj_blocks2)
        #make new local districts swapping the blocks
        new_d1 = district1.cblocks.copy()
        new_d2 = district2.cblocks.copy()
        new_d1.remove(adj1)
        new_d1.add(adj2)
        new_d2.remove(adj2)
        new_d2.add(adj1)
        #if the new districts are not contiguous, bail out
        shape1 = cascaded_union([b.shape for b in new_d1])
        shape2 = cascaded_union([b.shape for b in new_d2])
        if(not (isinstance(shape1,Polygon) and isinstance(shape2,Polygon))):
            return False
        #modify the districts to reflect the swapped blocks.
        district1.cblocks = new_d1
        district2.cblocks = new_d2
        district1.shape = shape1
        district2.shape = shape2
        adj_blocks1,adj_blocks2 = self.find_adjacent(district1,district2)
        self.adjacent_blocks[district1.index][district2.index] = adj_blocks1
        self.adjacent_blocks[district2.index][district1.index] = adj_blocks2
        return True

        
        
        
        
        
        
        
        
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
    district_list = list()
    district_num = 1
    for i in range(0,8,4):
        for j in range(0,8,4):
            district = make_dist (i, i+4, j, j+4, "{0}-{1}".format(name, district_num), all_cblocks)
            district_list.add(district)
            district_num += 1
    state = State(name, district_list, all_cblocks)
    return state 
    
def draw_state_grid(states, width, plot):
    height = len(states)//width
    i = 0
    j = 0
    import matplotlib.gridspec as gridspec
    gs = gridspec.GridSpec(width, height)
    gs.update(wspace=0,hspace=0)
    #plt.gca().set_aspect('equal','datalim')
    for state in states:
        ax = plot.subplot(gs[i,j])
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_color('none')
        ax.spines['right'].set_color('none')
        #ax.set_aspect('equal','datalim')
        ax.tick_params(axis='both',labelcolor='none',color='none')

        state.plot_state(ax)
        i = (i+1) % width
        if i == 0:
            j += 1
        
            

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

def simulation(New_list, number_district, number_samples = 100):  #generates sample lists of random districts w/ same demographics as given state
    test_list  = []
    fail_count = 0
    print ('Number of districts: ', number_district)
    while len(test_list) < number_samples:
        simulated_set = random.sample(New_list, number_district) #generates list of random districts
        if abs(sum([cblock.dems  for dist in simulated_set for cblock in dist.cblocks  ])/ 
                sum([cblock.population for dist in simulated_set for cblock in dist.cblocks ]) 
        - total_percent_dem) <= 0.05:    #allow for margin of error of 1% for the demographic breakdown of the simualated set
            for dist in simulated_set:  #counts how many seats in random set of districts are held by Democrats
                total_dem_seat = sum([cblock.dems for dist in simulated_set for cblock in dist.cblocks])
            test_list.append(total_dem_seat)
        else: 
            fail_count += 1     #keeps count of how many random sets of districts did not match state's demographics
    print ('fail_count: ', fail_count)
    #print (test_list)
    return (test_list)

state = input('Insert the abbreviation of the state: ', )
demographic_breakdown(state)

total_percent_dem = demographic_breakdown(state)[0]
total_percent_rep = demographic_breakdown(state)[1]


number_samples = 100

count_dist = collections.Counter([dist.name[:1] for dist in All_district])
number_district = count_dist.get(state)     #number of districts in given state 

test_list = simulation(New_list, number_district, number_samples)
print (test_list)


draw_state_grid(state_set,4,plt)

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

                
        

        

