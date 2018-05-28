#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:49:39 2017
@author: Brianna Bartz, Bill Retert, Ngan Tran, McKenzie Lamb
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
import math
import copy
from scipy import stats

#method = 'clustered_dems' #Population distribution
method = 'random'

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
            color = 'purple'
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
        self.calculate_demographics()
        self.calculate_winner()
        
    def calculate_demographics(self):
        self.dems = sum([cblock.dems for cblock in self.cblocks])
        self.reps = sum([cblock.reps for cblock in self.cblocks])
        self.population = self.dems + self.reps

    
    def calculate_winner(self):
        if self.dems > self.reps:
            self.winner = 'D'
        elif self.reps > self.dems:
            self.winner = 'R'
        else:
            self.winner = 'T'
        
    def __str__(self):
        return self.name
        
    def plot_district(self,plot):
        for block in self.cblocks:
            block.plot_block(plot)
        x,y=self.shape.exterior.xy
        plot.plot(x,y,linestyle='solid',color='white',lw=2)
        c = self.shape.centroid.coords[0]
        plot.text(c[0],c[1],self)

class State:
    def __init__(self, name, districts, all_cblocks):
        self.name = name 
        self.districts = districts
        self.shape = cascaded_union([district.shape for district in districts])
        self.all_cblocks = all_cblocks
        for cblocks in all_cblocks:
            for cblock in cblocks:
                cblock.state = self
#        self.adjacent_blocks = []
        index = 0
        for district in self.districts:
            district.index = index
            index += 1
#        self.initialize_adjacency()
        
    def initialize_adjacency(self):
        for district in self.districts:
            row = []
            for other_district in self.districts:
                adj = self.find_adjacent(district,other_district)[0]
                row.append(adj)
            self.adjacent_blocks.append(row)
            
            
        
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
        return adj_from, adj_to

    def pairwise_swap(self, district1, district2):
#        self.initialize_adjacency() #For testing.  Should not be needed.
        if (district1 is district2 or not is_adjacent(district1.shape,district2.shape)):
                return False
        #choose a random block in district1 which is adjacent to district2 and vice versa
        adj_blocks1, adj_blocks2 = self.find_adjacent(district1, district2)
        if len(adj_blocks1) == 0:
            print("No adjacency:", district1.name, district2.name)
            return False
#        adj_blocks2 = self.adjacent_blocks[district2.index][district1.index]
        adj1 = random.sample(adj_blocks1, 1)[0]
        adj2 = random.sample(adj_blocks2, 1)[0]
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
#        self.adjacent_blocks[district1.index][district2.index] = adj_blocks1
#        self.adjacent_blocks[district2.index][district1.index] = adj_blocks2
        return True
    
    #Not working yet.
    def central_gerrymander(self):
        dist_list = list(self.districts)
        all_cblocks = []
        for dist in dist_list:
            all_cblocks += dist.cblocks
        for dist in dist_list:
            dist.cblocks = set()
        for cblock in all_cblocks:
            c = cblock.shape.centroid.xy
            if (c[0][0] > 2 
                and c[0][0] < 6 
                and c[1][0] > 2
                and c[1][0] < 6):
                dist_list[0].cblocks.add(cblock)
            elif (c[0][0] > 6):
                dist_list[1].cblocks.add(cblock)
            elif (c[0][0] < 2):
                dist_list[2].cblocks.add(cblock)                
            elif (c[1][0] > 4):
                dist_list[3].cblocks.add(cblock) 
            else:
                print("error making districts", (c[0][0], c[1][0]))
                
    def reset_state(self):   #make state - state is 8x8
        district_set = set()
        district_num = 1
        for i in range(0,8,4):
            for j in range(0,8,4):
                district = make_dist (i, i+4, j, j+4, "{0}-{1}".format(name, district_num), self.all_cblocks) #establish state districts w/ name and cblocks
                district_set.add(district)
                district_num += 1
                
class Country:
        def __init__(self, name, all_districts, state_list):
            self.name = name
            self.all_districts = all_districts
            self.state_list = state_list
        
def make_cblocks(mean_affiliation = 50):   #create cblocks of one state  - cblocks are 1x1    
    cblock_array = []
    for i in range(8):
        row = []
        for j in range(8):
            if method == 'random':
                dems = 101
                while dems < 0 or dems > 100:  #random demographics of political affiliation       
                    dems = int(random.gauss(mean_affiliation, 10) + .5)
                    if dems == 50:
                        dems += random.choice([-1,1])
                    reps = 100 - dems
            elif method == 'clustered_dems':
                dems = 100 * math.exp(-((i-3.5)**2+(j-3.5)**2)/13)
                reps = 100 - dems
            shape = Polygon([(i,j), (i+1,j), (i+1,j+1), (i,j+1)]) #makes each cblock a 1x1 square
            row.append(CBlock(dems, reps, 100, shape))
        cblock_array.append(row)
    return cblock_array

def make_dist(min_i, max_i, min_j, max_j, name, cblock_array):  #make districts of one state - districts are 4x4
    cblock_set = set()
    dems = 0
    reps = 0
    for i in range(min_i, max_i):
        for j in range(min_j, max_j):
            cblock_set.add(cblock_array[i][j])   #create set of cblocks found in one district
    district = District(name, cblock_set)
    return district


def make_state(name, mean_affiliation = 50, plan = 'blocks'):   #make state - state is 8x8
    all_cblocks = make_cblocks(mean_affiliation)
    district_set = set()
    district_num = 1
    for i in range(0,8,4):
        for j in range(0,8,4):
            district = make_dist (i, i+4, j, j+4, "{0}-{1}".format(name, district_num), all_cblocks) #establish state districts w/ name and cblocks
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

def demographic_breakdown(state):
    total_percent_dems = sum([dist.dems for dist in state.districts]) / sum([dist.population for dist in state.districts])       
    total_percent_reps = sum([dist.reps for dist in state.districts]) / sum([dist.population for dist in state.districts])                                        
    return total_percent_dems, total_percent_reps


       
def simulation (outside_district_list, total_percent_dems, number_of_districts, number_samples):
    test_list  = []
    fail_count = 0
    while len(test_list) < number_samples:
        simulated_set = random.sample(outside_district_list, number_of_districts ) 
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

def complete_simulation(outside_district_sets, total_percent_dems):
    test_list  = [] 
    for simulated_set in outside_district_sets:
            if abs(sum([dist.dems for dist in simulated_set])/ sum([dist.population for dist in simulated_set]) 
        - total_percent_dems) <= 0.01:    #allow for margin of error of 1% for the demographic breakdown of the simualated set
                test_list.append(sum([1 for dist in simulated_set if dist.winner == "D"]))
    print("Outside District Sets: ", len(outside_district_sets))
    return test_list

def calculate_p_value (sample_list, current_dem_seats, mean_test):
    extreme = 0
    if current_dem_seats < mean_test:
        for i in sample_list:
            if i <= current_dem_seats:
                extreme += 1        #count the outcomes as least as extreme as the current one in order to calculate p_value
        p_value =  -extreme / len(sample_list)
        print ('extreme count: ', extreme)
        return (p_value)   
        
    else:
        for i in sample_list:
            if i >= current_dem_seats:
                extreme += 1
        p_value = extreme / len(sample_list)
        print ('extreme count: ', extreme)
        return (p_value)   
   
#----Create Gerrymandria----          
#state_names = "ABCDEFGHIJKLMNOP"
#state_list = []
#for name in state_names:
#    if name in "ABCDEFG":
#        state_list.append(make_state(name, mean_affiliation = 50))
#    else:
#        state_list.append(make_state(name, mean_affiliation = 50))
#all_districts = []
#for state in state_list:
#     for district in state.districts:
#          all_districts.append(district)                 #A list of all district objects in Gerrymandria

#-----Rebuild Saved Country-----
#file = open("MajorityGerrymander", 'rb')  
#Country = pickle.load(file) 
#file.close()
#state_list = Country['state_list']
#all_districts = Country['all_districts']
#file = open("StateB.pkl", 'rb')  
#state = pickle.load(file) 
#file.close()
#state_list[1] = state

#-----Print Demographic Info-----
for state in state_list:
    print (demographic_breakdown(state))       
#print (Gerrymandria_demographic()) 
#state.plot_state(plt.subplot())          

#-----Wang's Test of Effects-----
def EffectsTest(state, number_of_samples=1000):
    outside_district_list = [dist for dist in all_districts if dist.name[:1] != state.name]
    current_dem_seats = MaxDemFitness(state)
    number_of_districts = len([state.districts])
    total_percent_dems = demographic_breakdown(state)[0]
    outside_district_sets = list(itertools.combinations(outside_district_list, 4))
    random.shuffle(outside_district_sets)
#    test_list = simulation(outside_district_list, total_percent_dems, number_of_districts, number_of_samples)
    test_list = complete_simulation(outside_district_sets, total_percent_dems)
    mean_test = sum([n for n in test_list])/len(test_list)     
    sd = statistics.stdev([n for n in test_list])
    p_value = calculate_p_value(test_list, current_dem_seats, mean_test)
#    print ('Current democratic seats: ', current_dem_seats)
#    print ('Percentage of democrats in the state: ', total_percent_dems)
#    print ('Mean: ', mean_test)
    print ('p_value: ', p_value)
#    print ('standard deviation: ', sd)
    return p_value


def MaxDemFitness(state):
    for district in state.districts:
        district.calculate_demographics()
        district.calculate_winner()
    return sum([1 for district in state.districts if district.winner == 'D' ])

def MaxRepFitness(state):
    for district in state.districts:
        district.calculate_demographics()
        district.calculate_winner()
    return sum([1 for district in state.districts if district.winner == 'R' ])

def EfficiencyGap(state):
    for district in state.districts:
        district.calculate_demographics()
        district.calculate_winner()
    r_waste = 0
    d_waste = 0
    for dist in state.districts:
       if dist.winner == 'D':
           d_waste += dist.dems - 0.5 * dist.population
           r_waste += dist.reps
       elif dist.winner == 'R':
           d_waste += dist.dems 
           r_waste += dist.reps - 0.5 * dist.population
       else:
            d_waste += dist.dems 
            r_waste += dist.reps
       overall_total_vote = sum([dist.population for dist in state.districts])            
       return (d_waste - r_waste) / overall_total_vote

def SimulatedAnnealing(state, FitnessFunction):
    best_state = copy.deepcopy(state)
    fitness = FitnessFunction(state)
    print("Initial Fitness = ", fitness)
    max_steps = 100
    max_tries= 300
    steps = 0
    tries = 0
    while steps < max_steps and tries < max_tries:
        print('.', end='')
        DoSwaps(state, 1)
        new_fitness = FitnessFunction(state)
        tries += 1
        #print("Factor = ", math.exp(-(10*tries/max_tries)**2))
        p = random.random() * math.exp(-(tries/max_tries)**2)
#        print('p = ', p)
        if new_fitness > fitness:
            best_state = copy.deepcopy(state)
        if new_fitness >= fitness or p > 1:
            print("New Fitness = ", new_fitness)
            fitness = new_fitness
            steps += 1
    print('\n')
    return best_state

def RandomWalk(state, FitnessFunction):
    best_state = copy.deepcopy(state)
    fitness = FitnessFunction(state)
    print("Initial Fitness = ", fitness)
    max_tries= 1000
    tries = 0
    while tries < max_tries:
#        print("Trying . . .")
        DoSwaps(state, 1)
        new_fitness = FitnessFunction(state)
        tries += 1
#        print(new_fitness, end=' ')
        if new_fitness > fitness:
            best_state = copy.deepcopy(state)
        if new_fitness == 3:
            best_state = copy.deepcopy(state)
            return best_state
    print('\n')
    return best_state
    
def DoSwaps(state, number_of_swaps = 3):
    max_tries = 100
    swap_count = 0
    while swap_count < number_of_swaps:
        ps = False
        try_count = 0
        while ps == False and try_count < max_tries:
            [dist1, dist2] = random.sample(state.districts, 2)
            ps = state.pairwise_swap(dist1, dist2)
            try_count += 1
        if try_count == max_tries and ps == False:
            print("Failed to swap.", dist1.name, dist2.name)
        else:
            swap_count += 1

def GerrymanderMajority():
    for state in state_list:
        if state.name not in "ABCDEFG":
            RandomWalk(state, MaxRepFitness)
    
def MeanMedian(state):
    dem_vote_list = [dist.dems for dist in state.districts]
    mean = sum(dem_vote_list)/len(state.districts)
    median = statistics.median(dem_vote_list)
    return 0.5708 * (mean - median)/stats.sem(dem_vote_list) 

def TTest(state):
    dem_props = [dist.dems/dist.population for dist in state.districts if dist.winner == 'D']
    rep_props = [dist.reps/dist.population for dist in state.districts if dist.winner == 'R']
    return(stats.ttest_ind(dem_props,rep_props, equal_var = False))
    
def PickleCountry(country):
    import pickle
    fileObject = open("MajorityGerrymander2",'wb')
    pickle.dump(country, fileObject)
    fileObject.close() 
    
#Recalculate demographics for each district in state
for district in state.districts:
    district.calculate_demographics()
    district.calculate_winner()

outfile = open('gerrymander_record', 'w')
    
#Stats at the beginning
print("Beginning . . . ", file=outfile)
print("Total Dem Seats = ", sum([MaxDemFitness(state) for state in state_list]), file=outfile)

#for state in state_list:
#    print("**********", file=outfile)
#    print("State Name = ", state.name, file=outfile)
#    initial_seats = MaxDemFitness(state)
#    print("Initial Dem Seats = ", initial_seats, file=outfile)
#    print("---First Effects Test---")
#    print("p-value = ", EffectsTest(state), file=outfile)
#    mm_initial = MeanMedian(state)
#    print("Mean - Median = ", mm_initial, file=outfile)
#    if state.name not in 'ABCDEFG':
#        state = RandomWalk(state, MaxRepFitness)
#    else:
#        state = RandomWalk(state, MaxDemFitness)
#    ##state = SimulatedAnnealing(state, MeanMedian)
#    print("---Second Effects Test---")
#    print("p-value = ", EffectsTest(state), file=outfile)
#    #print("TTest = ", TTest(state))
#    mm_final = MeanMedian(state)
#    print("Mean - Median = ", mm_final, file=outfile)
#    final_seats = MaxDemFitness(state)
#    print("Final Dem Seats = ", final_seats)
#    print("Seat Change = ",  final_seats - initial_seats, file=outfile)
##    print("p-value change =", p_initial - p_final)
#    print("MeanMedian change =", mm_initial - mm_final, file=outfile)
#    print("Total Dem Seats = ", sum([MaxDemFitness(state) for state in state_list]), file=outfile)
#    draw_state_grid(state_list, 4, plt)
#    plt.savefig('gerrymandered_' + state.name + '.jpg', dpi=1000)

#mg_country = Country("MG", all_districts, state_list)
#PickleCountry(mg_country)
infile = open("MajorityGerrymander2", 'rb')
mg_country = pickle.load(infile)
all_districts = mg_country.all_districts
state_list = mg_country.state_list

print("-------2nd Run----------")

for i in range(len(state_list)):
    if state_list[i] .name in 'ABCDEFG':
        print("**********", file=outfile)
        print("State Name = ", state_list[i] .name, file=outfile)
        initial_seats = MaxDemFitness(state_list[i])
        print("Initial Dem Seats = ", initial_seats, file=outfile)
        print("---First Effects Test---")
        print("p-value = ", EffectsTest(state_list[i]), file=outfile)
        mm_initial = MeanMedian(state_list[i] )
        print("Mean - Median = ", mm_initial, file=outfile)
        state_list[i].reset_state() #Cheat by restarting at generic state
        state_list[i]  = RandomWalk(state, MaxRepFitness)
        ##state = SimulatedAnnealing(state, MeanMedian)
        print("---Second Effects Test---")
        print("p-value = ", EffectsTest(state_list[i]), file=outfile)
        #print("TTest = ", TTest(state))
        mm_final = MeanMedian(state_list[i])
        print("Mean - Median = ", mm_final, file=outfile)
        final_seats = MaxDemFitness(state_list[i])
        print("Final Dem Seats = ", final_seats)
        print("Seat Change = ", final_seats - initial_seats, file=outfile)
    #    print("p-value change =", p_initial - p_final)
        print("MeanMedian change =", mm_initial - mm_final, file=outfile)
        print("Total Dem Seats = ", sum([MaxDemFitness(state) for state in state_list]), file=outfile)
        draw_state_grid(state_list, 4, plt)
        plt.savefig('2nd_run_gerrymandered_' + state_list[i].name + '.jpg', dpi=1000)   
    
infile.close()
outfile.close()
#Stats at the end
#print("Total Dem Seats = ", sum([MaxDemFitness(state) for state in state_list]))


#draw_state_grid(state_list, 4, plt)
#plt.savefig('gerrymandered_' + state.name + '.jpg', dpi=1000)

#print("Initial Dem Seats = ", MaxDemFitness(state))
#state = SimulatedAnnealing(state, EfficiencyGap)
#print("Final Dem Seats = ", MaxDemFitness(state))


#state.plot_state(plt.subplot())
#plt.savefig('once_gerrymandered.svg')  
#plt.savefig('state_' + state.name + '_gerrymandered.jpg', dpi=1000)
#GerrymanderMajority()    
#draw_state_grid(state_list, 4, plt)
#plt.savefig('MajorityPlusBA.jpg', dpi=1000)
#plt.savefig('majority_gerrymander.jpg', dpi=300)
#PickleMajorityGerrymander()
       
          
          
          
          


