#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:49:39 2017

@author: bribartz
"""
#Gerrymandria has 16 states, each states has 4 districts and each districts consists of 16 census blocks

from shapely.geometry import Polygon
from shapely.geometry import Point
from shapely.ops import cascaded_union
import matplotlib.pyplot as plt
from descartes.patch import PolygonPatch
import random
import collections
import statistics

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
    def __init__(self, name, cblocks, dems, reps, winner):
        self.name = name
        self.cblocks = cblocks
        self.shape = cascaded_union([cblock.shape for cblock in cblocks])
        self.dems = dems
        self.reps = reps
        self.population = sum([block.population for block in cblocks])
        self.winner = winner
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
                dems = int(random.gauss(50, 10) + .5)
                reps = 100 - dems
                shape = Polygon([(i,j), (i+1,j), (i+1,j+1), (i,j+1)])
                row.append(CBlock(dems, reps, 100, shape))
        cblock_array.append(row)
    return cblock_array

def make_dist(min_i, max_i, min_j, max_j, name, cblock_array):
    cblock_set = set()
    dems = 0
    reps = 0
    for i in range(min_i, max_i):
        for j in range(min_j, max_j):
            cblock_set.add(cblock_array[i][j])
            dems += cblock_array[i][j].dems
            reps += cblock_array[i][j].reps
    if dems > reps:
        winner = "D"
    elif reps > dems:
        winner = "R"
    else:
        winner = "?"
    district = District(name, cblock_set, dems, reps, winner)
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
state_set = {make_state(name) for name in state_names}    #A list of all state objects in Gerrymandria
All_district = []
for state in state_set:
     for district in state.districts:
          All_district.append(district)                   #A list of all district objects in Gerrymandria
          
          
def Gerrymandria_demographic():                            #This function will give us the demographic breakdown of Gerrymandria
    all_dems = 0
    all_reps = 0
    for state in state_set:
        for district in state.districts:
            for cblock in district.cblocks:
                all_dems += cblock.dems
                all_reps += cblock.reps
    total_pop = (all_dems+all_reps)
    percent_dems_Gerrymandria = all_dems / total_pop
    percent_reps_Gerrymandria = all_reps / total_pop
    return percent_dems_Gerrymandria, percent_reps_Gerrymandria
print (Gerrymandria_demographic())           #The results are 0.4978865879685357, 0.5021134120314642 

def demographic_breakdown(state):
    total_dems = 0
    total_reps = 0
    total_pop = 0
    for i in range(len(All_district)):
        if All_district[i].name[:1] == state:   
            total_dems += All_district[i].dems 
            total_reps += All_district[i].reps
            total_pop += All_district[i].population       
    total_percent_dems = total_dems / total_pop       
    total_percent_reps = total_reps / total_pop                                        
    return total_percent_dems, total_percent_reps

for state in state_set:
    print (demographic_breakdown(state.name))       #Yay!! It worked!! 


       
def simulation (new_list, number_district, number_samples):
    test_list  = []
    fail_count = 0
    while len(test_list) < number_samples:
        simulated_set = random.sample(new_list, number_district ) 
        if abs(sum([dist.dems for dist in simulated_set])/ sum([dist.population for dist in simulated_set]) 
        - total_percent_dems) <= 0.01:    #allow for margin of error of 1% for the demographic breakdown of the simualated set
            total_dem_seat = 0
            for dist in simulated_set:  #counts how many seats in random set of districts are held by Democrats
                if dist.winner == "D":
                    total_dem_seat += 1
            test_list.append(total_dem_seat)
        else: 
            fail_count += 1     #keeps count of how many random sets of districts did not match state's demographics
    print ('fail_count: ', fail_count)
    return test_list

def calculate_p_value (sets):
    extreme = 0
    if current_dem_seat < mean_test:
        for i in sets:
            if i <= current_dem_seat:
                extreme += 1        #count the outcomes as least as extreme as the current one in order to calculate p_value
    else:
        for i in sets:
            if i >= current_dem_seat:
                extreme += 1
    p_value = extreme / number_samples
    print ('extreme count: ', extreme)
    return (p_value)      
          

number_samples = 1000
state = input('Insert the abbreviation of the state: ', )
count_dist = collections.Counter([dist.name[:1] for dist in All_district])
number_district = count_dist.get(state)     #number of districts in given state
total_percent_dems = demographic_breakdown(state)[0]
total_percent_reps = demographic_breakdown(state)[1]  
new_list = []
current_dem_seat = 0
for dist in All_district:       #creates new list of districts to make up random 
    if dist.name[:1] != state:  #list of districts that discludes districts from given state   
        new_list.append(dist) 
for dist in All_district:       #counts how many seats currently held in by democrats in given state
    if dist.name[:1] == state and dist.winner == "D":
        current_dem_seat += 1  
test_list = simulation(new_list, number_district, number_samples)
mean_test = sum([n for n in test_list])/number_samples     
sd = statistics.stdev([n for n in test_list])
p_value = calculate_p_value(test_list)
print ('Current democratic seats: ', current_dem_seat)
print ('Percentage of democrats in the state: ', total_percent_dems)
print ('Mean: ', mean_test)
print ('p_value: ', p_value)
print ('standard deviation: ', sd)
  
draw_state_grid(state_set,4,plt)
          
          
          
          
          

##
#
#number_samples = 100

#count_dist = collections.Counter([dist.name[:1] for dist in All_district])
#print (count_dist)
    

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


        

        

