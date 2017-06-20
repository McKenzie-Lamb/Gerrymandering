#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:49:39 2017

@author: bribartz
"""

from shapely.geometry import Polygon
from shapely.ops import cascaded_union
import matplotlib.pyplot as plt
from descartes.patch import PolygonPatch
import random
import collections

class CBlock:
    def __init__(self, dems, reps, population, shape):
        self.dems = dems 
        self.reps = reps 
        self.population = 100
        self.shape = shape
        
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


class District:
    def __init__(self, name, cblocks):
        self.name = name
        self.cblocks = cblocks
        self.shape = cascaded_union([cblock.shape for cblock in cblocks])
        
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
        
    def __str__(self):
        return self.name
        
    def plot_state(self,plot):
        for district in self.districts:
            district.plot_district(plot)
        x,y = self.shape.exterior.xy
        plot.plot(x,y,color='black',lw=3)
        
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
make_cblocks()
demographic_breakdown('A')
#total_percent_dem = demographic_breakdown(state)[0]
#total_percent_rep = demographic_breakdown(state)[1]


number_samples = 100

count_dist = collections.Counter([dist.name[:1] for dist in All_district])
    
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

                
        

        

