#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:49:39 2017

@author: bribartz
"""
#Gerrymandria has 16 states, each states has 4 districts and each districts consists of 16 census blocks
from shapely.geometry import Polygon
from shapely.ops import cascaded_union
import random
import statistics

class CBlock:
    def __init__(self, dems, reps, population, shape):
        self.dems = dems 
        self.reps = reps 
        self.population = population
        self.shape = shape

class District:
    def __init__(self, name, cblocks, dems, reps, population, winner):
        self.name = name
        self.cblocks = cblocks
        self.shape = cascaded_union([cblock.shape for cblock in cblocks])
        self.dems = dems
        self.reps = reps
        self.population = population
        self.winner = winner

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
                dems = int(random.gauss(50, 10) + 0.5)              #Round to the nearest int
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
    else:
        winner = "R"
    district = District(name, cblock_set, dems, reps, 1600, winner)
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
    percent_dems_Gerrymandria = all_dems / 102400
    percent_reps_Gerrymandria = all_reps / 102400
    return percent_dems_Gerrymandria, percent_reps_Gerrymandria
#print (Gerrymandria_demographic())           #The results are 0.4978865879685357, 0.5021134120314642 

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
       
def simulation (new_list, number_samples):
    test_list  = []
    fail_count = 0
    while len(test_list) < number_samples:
        simulated_set = random.sample(new_list, 4) 
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
    return (test_list)      

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
state = "A"
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
test_list = simulation(new_list, number_samples)
mean_test = sum([n for n in test_list])/number_samples     
sd = statistics.stdev(n for n in test_list)
p_value = calculate_p_value(test_list)
print ('Current democratic seats: ', current_dem_seat)
print ('Percentage of democrats in the state: ', total_percent_dems)
print ('Mean: ', mean_test)
print ('p_value: ', p_value)
print ('standard deviation: ', sd)
  
          
          
          
          
          
          

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


        

        

