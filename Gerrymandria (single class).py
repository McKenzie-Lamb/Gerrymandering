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
#import collections
import statistics
import math
import copy
from scipy import stats
import itertools
import pickle

#method = 'clustered_dems' #Population distribution
method = 'random'

#Check adjacency of shape1 and shape2.  Touching at a single point
#does not count as adjacent.
def is_adjacent(shape1, shape2):
        return (shape1 is not shape2 and shape1.touches(shape2) 
                 and not isinstance(shape1.intersection(shape2),Point))

#Census Block class.  Holds information about shape and demographics.
class CBlock:
    def __init__(self, dems, reps, population, shape, state):
        self.dems = dems 
        self.reps = reps 
        self.population = population
        self.shape = shape
        self.state = None
        self.district = None
        self.state = state
                
        
    def __str__(self):
        return "({0}-{1})".format(self.dems,self.reps)
        
    #Takes a matplotlib plot (plot) and adds a PolygonPatch to it using its shape and demographics.
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
        
    #Check whether other block is adjacent to self.
    def is_adjacent(self, other_block):
        return is_adjacent(self.shape,other_block.shape)


#Holds a collection of census blocks.
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
        
    #Calculate proportions of Democrats and Republicans.
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
        
    #Takes a matplotlib plot and adds all of its census blocks; plots name.
    def plot_district(self,plot):
        for block in self.cblocks:
            block.plot_block(plot)
        x,y=self.shape.exterior.xy
        plot.plot(x,y,linestyle='solid',color='white',lw=2)
        
        #Plot district name at center of mass.
        c = self.shape.centroid.coords[0]
        plot.text(c[0],c[1],self) 

#Holds districts.  Creates census blocks and then assigns them to districts.
class State:
    def __init__(self, name, districts = []):
        self.name = name 
        self.districts = districts
        self.make_cblocks()
        self.make_districts()
        self.shape = cascaded_union([district.shape for district in self.districts])


#        self.adjacent_blocks = []
        index = 0
        for district in self.districts:
            district.index = index
            index += 1
#        self.initialize_adjacency()
        

    #For testing only.
#    def initialize_adjacency(self):
#        for district in self.districts:
#            row = []
#            for other_district in self.districts:
#                adj = self.find_adjacent(district,other_district)[0]
#                row.append(adj)
#            self.adjacent_blocks.append(row)
    
    #Create all census blocks in the state and store them in an array.
    def make_cblocks(self, mean_affiliation = 50):      
        self.cblocks = []
        for i in range(8):
            row = []
            for j in range(8):
                if method == 'random': #Random distribution.
                    dems = 101
                    while dems < 0 or dems > 100:       
                        dems = int(random.gauss(mean_affiliation, 10) + .5)
                        if dems == 50:
                            dems += random.choice([-1,1])
                        reps = 100 - dems
                elif method == 'clustered_dems': #Democrats clustered around a point.
                    dems = 100 * math.exp(-((i-3.5)**2+(j-3.5)**2)/13)
                    reps = 100 - dems
                shape = Polygon([(i,j), (i+1,j), (i+1,j+1), (i,j+1)]) #Makes each cblock a 1x1 square
                row.append(CBlock(dems, reps, 100, shape, self))
            self.cblocks.append(row)
    
    #Create all districts by calling make_dist repeatedly.
    def make_districts(self):
        self.districts = []
        district_num = 1
        for i in range(0,8,4):
            for j in range(0,8,4):
                self.make_dist (i, i+4, j, j+4, "{0}-{1}".format(self.name, district_num)) #establish state districts w/ name and cblocks
                district_num += 1            
        
    #Create a single district.  Assign a 4x4 set of census blocks to the district.
    def make_dist(self, min_i, max_i, min_j, max_j, name):  
        cblock_set = set()
        for i in range(min_i, max_i):
            for j in range(min_j, max_j):
                cblock_set.add(self.cblocks[i][j])   
        self.districts.append(District(name, cblock_set))
            
    def __str__(self):
        return self.name
        
    def plot_state(self, plot):
        for district in self.districts:
            district.plot_district(plot)
        x,y = self.shape.exterior.xy
        plot.plot(x,y,color='black',lw=3)

    #Find all census blocks that can be swapped from district1 to district2;
    #Find all census blocks that can be swapped from district2 to district1;
    #Return both lists.
    def find_adjacent(self, district1, district2):
        adj_from = set()
        adj_to = set()
        if district1 is not district2: #district1=district2 would produce weirdness.                    
            for block in district1.cblocks:
                for other_block in district2.cblocks:
                    if block.is_adjacent(other_block):
                        adj_from.add(block)
                        adj_to.add(other_block)
        return adj_from, adj_to

    #Try to swap a pair of census blocks between district1 and district2.
    #Fails if the swap tried produces discontiguous districts.
    def pairwise_swap(self, district1, district2, contiguous = True):
        if (district1 is district2 or not is_adjacent(district1.shape,district2.shape)):
                return False
        #Choose a random block in district1 which is adjacent to district2 and vice versa
        adj_blocks1, adj_blocks2 = self.find_adjacent(district1, district2)
        if len(adj_blocks1) == 0:
            print("No adjacency:", district1.name, district2.name)
            return False
        adj1 = random.sample(adj_blocks1, 1)[0]
        adj2 = random.sample(adj_blocks2, 1)[0]
        
        #Make new local districts by swapping the blocks.
        new_d1 = district1.cblocks.copy()
        new_d2 = district2.cblocks.copy()
        new_d1.remove(adj1)
        new_d1.add(adj2)
        new_d2.remove(adj2)
        new_d2.add(adj1)
        
        if contiguous == True:
            #If the new districts are not contiguous, bail out
            shape1 = cascaded_union([b.shape for b in new_d1])
            shape2 = cascaded_union([b.shape for b in new_d2])
            if(not (isinstance(shape1,Polygon) and isinstance(shape2,Polygon))):
                return False
        
        #Modify the districts to reflect the swapped blocks.
        district1.cblocks = new_d1
        district2.cblocks = new_d2
        district1.shape = shape1
        district2.shape = shape2
        adj_blocks1,adj_blocks2 = self.find_adjacent(district1,district2)
#        self.adjacent_blocks[district1.index][district2.index] = adj_blocks1
#        self.adjacent_blocks[district2.index][district1.index] = adj_blocks2
        return True
    
#    #Not working yet.
#    def central_gerrymander(self):
#        dist_list = list(self.districts)
#        all_cblocks = []
#        for dist in dist_list:
#            all_cblocks += dist.cblocks
#        for dist in dist_list:
#            dist.cblocks = set()
#        for cblock in all_cblocks:
#            c = cblock.shape.centroid.xy
#            if (c[0][0] > 2 
#                and c[0][0] < 6 
#                and c[1][0] > 2
#                and c[1][0] < 6):
#                dist_list[0].cblocks.add(cblock)
#            elif (c[0][0] > 6):
#                dist_list[1].cblocks.add(cblock)
#            elif (c[0][0] < 2):
#                dist_list[2].cblocks.add(cblock)                
#            elif (c[1][0] > 4):
#                dist_list[3].cblocks.add(cblock) 
#            else:
#                print("error making districts", (c[0][0], c[1][0]))

    def demographic_breakdown(self):
        total_percent_dems = sum([dist.dems for dist in self.districts]) / sum([dist.population for dist in self.districts])       
        total_percent_reps = sum([dist.reps for dist in self.districts]) / sum([dist.population for dist in self.districts])                                        
        return total_percent_dems, total_percent_reps
    
    
    def EfficiencyGap(self):
        for district in self.districts:
            district.calculate_demographics()
            district.calculate_winner()
        r_waste = 0
        d_waste = 0
        for dist in self.districts:
           if dist.winner == 'D':
               d_waste += dist.dems - 0.5 * dist.population
               r_waste += dist.reps
           elif dist.winner == 'R':
               d_waste += dist.dems 
               r_waste += dist.reps - 0.5 * dist.population
           else:
                d_waste += dist.dems 
                r_waste += dist.reps
           overall_total_vote = sum([dist.population for dist in self.districts])            
           return (d_waste - r_waste) / overall_total_vote
       
    #Recalculate demographics for each district in state
    def RecalculateDistrictDemographics(self):
        for district in self.districts:
            district.calculate_demographics()
            district.calculate_winner()

        
    def DoSwaps(self, number_of_swaps = 3, contiguous = True):
        max_tries = 100
        swap_count = 0
        while swap_count < number_of_swaps:
            ps = False
            try_count = 0
            while ps == False and try_count < max_tries:
                [dist1, dist2] = random.sample(self.districts, 2)
                ps = self.pairwise_swap(dist1, dist2, contiguous)
                try_count += 1
            if try_count == max_tries and ps == False:
                print("Failed to swap.", dist1.name, dist2.name)
            else:
                swap_count += 1
                
    def MaxDemFitness(self):
        for district in self.districts:
            district.calculate_demographics()
            district.calculate_winner()
        return sum([1 for district in self.districts if district.winner == 'D' ])
    
    def MaxRepFitness(self):
        for district in self.districts:
            district.calculate_demographics()
            district.calculate_winner()
        return sum([1 for district in self.districts if district.winner == 'R' ])
    
    def MeanMedian(self):
        dem_vote_list = [dist.dems for dist in self.districts]
        mean = sum(dem_vote_list)/len(self.districts)
        median = statistics.median(dem_vote_list)
        return 0.5708 * (mean - median)/stats.sem(dem_vote_list) 
    

 #Stores states and everything in them.  Carries out gerrymandering, effects test, t-test.       
class Country:
    def __init__(self, name, all_districts = [], state_list = []):
        self.name = name
        self.state_list = state_list 
        self.make_states()
        
        #Make a list of all districts in all states.
        self.all_districts = []
        for state in state_list:
            for district in state.districts:
                self.all_districts.append(district)
        
        
    def make_states(self):
        state_names = "ABCDEFGHIJKLMNOP"
        for name in state_names:
            self.state_list.append(State(name))

                           
    
    def draw_state_grid(self, width, plot):
        height = len(self.state_list)//width
        i = 0
        j = 0
        import matplotlib.gridspec as gridspec
        gs = gridspec.GridSpec(width, height)
        gs.update(wspace=0,hspace=0)
        #plt.gca().set_aspect('equal','datalim')
        for state in self.state_list:
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
    #This function will give us the demographic breakdown of Gerrymandria              
    def Gerrymandria_demographic(self):           
        all_dems = 0
        all_reps = 0
        for state in self.state_list:
            for district in state.districts:
                for cblock in district.cblocks:
                    all_dems += cblock.dems
                    all_reps += cblock.reps
        total_pop = (all_dems+all_reps)
        percent_dems_Gerrymandria = all_dems / total_pop
        percent_reps_Gerrymandria = all_reps / total_pop
        return percent_dems_Gerrymandria, percent_reps_Gerrymandria    
    
           
    def GenerateComps(outside_district_list, total_percent_dems, number_of_districts, number_samples):
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
    
    def GenerateAllComps(self, outside_district_sets, total_percent_dems):
        test_list  = [] 
        for simulated_set in outside_district_sets:
                if abs(sum([dist.dems for dist in simulated_set])/ sum([dist.population for dist in simulated_set]) 
            - total_percent_dems) <= 0.01:    #allow for margin of error of 1% for the demographic breakdown of the simualated set
                    test_list.append(sum([1 for dist in simulated_set if dist.winner == "D"]))
        print("Outside District Sets: ", len(outside_district_sets))
        return test_list
    
    def calculate_p_value (self, sample_list, current_dem_seats, mean_test):
        extreme = 0
        if current_dem_seats < mean_test:
            for i in sample_list:
                if i <= current_dem_seats:
                    extreme -= 1        #count the outcomes as least as extreme as the current one in order to calculate p_value
        else:
            for i in sample_list:
                if i >= current_dem_seats:
                    extreme += 1
        p_value = extreme / len(sample_list)
        print ('extreme count: ', extreme)
        return (p_value)   

#-----Print Demographic Info-----
    def PrintDemographics(self):        
        for state in self.state_list:
            print (state.name, state.demographic_breakdown())  
            
    def TotalDemSeats(self):
        total_dem_seats = 0
        for state in self.state_list:
            for dist in state.districts:
                if dist.winner == 'D':
                    total_dem_seats += 1
        return total_dem_seats
    
    #Not applicable unless each party wins at least 2 seats.
    def TTest(self, state):
        dem_props = [dist.dems/dist.population for dist in state.districts if dist.winner == 'D']
        rep_props = [dist.reps/dist.population for dist in state.districts if dist.winner == 'R']
        return(stats.ttest_ind(dem_props,rep_props, equal_var = False))
        
    def PickleCountry(self, filename):
        import pickle
        fileObject = open(filename,'wb')
        pickle.dump(self, fileObject)
        fileObject.close() 
        
      #-----Wang's Test of Effects-----
    def EffectsTest(self, state, number_of_samples=1000):
        state.RecalculateDistrictDemographics()
        outside_district_list = []
        for other_state in self.state_list:
            if other_state != state:
                for dist in other_state.districts: 
                    outside_district_list.append(dist)
        current_dem_seats = sum([1 for district in state.districts if district.winner == 'D' ])
#        number_of_districts = len([state.districts])
        total_percent_dems = state.demographic_breakdown()[0]
        
        #Generate list of all sets of 4 districts from outside State.
        outside_district_sets = list(itertools.combinations(outside_district_list, 4))
        
        #Find all comparable district sets.
        test_list = self.GenerateAllComps(outside_district_sets, total_percent_dems)
        
        #Calculate stats.
        mean_test = sum([n for n in test_list])/len(test_list)     
        sd = statistics.stdev([n for n in test_list])
        p_value = self.calculate_p_value(test_list, current_dem_seats, mean_test)
        
        #Print results (primarily for testing).
        print ('Current democratic seats: ', current_dem_seats)
        print ('Percentage of democrats in the state: ', total_percent_dems)
        print ('Mean: ', mean_test)
        print ('p_value: ', p_value)
        print ('standard deviation: ', sd)
        self.PlotHistogram(test_list)
        return p_value
    
    #Show distribution of # of dem seats in comparable district sets.
    def PlotHistogram(self, test_list):
        n, bins, patches = plt.hist(test_list, 50, normed=1, facecolor='green', alpha=1)
        plt.grid(True)
        plt.show()

    #Gerrymander one more than half of the states in the country to favor Republicans;
    #Gerrymander the rest to favor Democrats.
    def GerrymanderMajority(self):
        for i in range(len(self.state_list)):
            print("State Name = ", self.state_list[i].name)
            if self.state_list[i].name in "ABCDEFG":
                self.state_list[i] = self.SimulatedAnnealingDem(self.state_list[i])
            else:
                self.state_list[i] = self.SimulatedAnnealingRep(self.state_list[i])

    #Gerrymander exactly half of the states in the country to favor Republicans;
    def GerrymanderHalf(self):
        for i in range(len(self.state_list)):
            print("State Name = ", self.state_list[i].name)
            if self.state_list[i].name not in "ABCDEFGH":
                self.state_list[i] = self.SimulatedAnnealingRep(self.state_list[i])

    #Gerrymander state to favor of Republicans.    
    def SimulatedAnnealingRep(self, state, threshold = 0.9):
        current_state = copy.deepcopy(state)
        fitness = current_state.MaxRepFitness()
        print("Initial Fitness = ", fitness)
        max_tries= 100 #Set bailout threshold so we don't go on foreover.
        tries = 0
        while tries < max_tries:
            
            #Generate value to determine whether to jitter.
            p = random.random() * math.exp(-(tries/max_tries)**2)
            fitness = current_state.MaxRepFitness()
            if fitness == 4:
                print("Final Fitness = ", fitness)
                return current_state
#            print("Fitness = ", fitness)
            new_state = copy.deepcopy(current_state)
#            print("Trying . . .")
            new_state.DoSwaps(3) #Make one or more swaps of census blocks between districts.
            new_fitness = new_state.MaxRepFitness() #Recalculate fitness.
            tries += 1
            
            #Move if fitness improves or if jitter value exceeds threshold.
            if new_fitness > fitness or p > threshold:
                fitness = new_fitness
                current_state = new_state
        print('Ran out of tries . . .')
        print("Final Fitness = ", current_state.MaxRepFitness())
        return current_state

    #Gerrymander state to favor of Democrats.  
    #(Basically the same as SimulatedAnnealingRep: should reorganize.)   
    def SimulatedAnnealingDem(self, state, threshold = 0.9, contiguous = True):
        current_state = copy.deepcopy(state)
        fitness = current_state.MaxDemFitness()
        print("Initial Fitness = ", fitness)
        max_tries= 100
        tries = 0
        while tries < max_tries:
            p = random.random() * math.exp(-(tries/max_tries)**2)
            fitness = current_state.MaxDemFitness()
            if fitness == 4:
                print("Final Fitness = ", fitness)
                return current_state
#            print("Fitness = ", fitness)
            new_state = copy.deepcopy(current_state)
#            print("Trying . . .")
            new_state.DoSwaps(3, contiguous)
            new_fitness = new_state.MaxDemFitness()
            tries += 1
            if new_fitness > fitness or p >threshold:
                fitness = new_fitness
                current_state = new_state
        print('Ran out of tries . . .')
        print("Final Fitness = ", current_state.MaxDemFitness())
        return current_state

#Pickle a country in which the majority has been gerrymandered in favor of 
#Republicans and the rest have been gerrymandered in favor of Democrats.
def RecordMajorityGerrymander():
    outFile = open("majority_gerrymander_record.txt", 'w')
    GMA = Country("Gerrymandria")   
    GMA.PrintDemographics()
    GMA.draw_state_grid(4, plt)
    plt.savefig('initial.jpg', dpi=1000)
    
    print("Initial Dem Seats = ", GMA.TotalDemSeats(), file=outFile)
    GMA.GerrymanderMajority()
    GMA.draw_state_grid(4, plt)
    plt.savefig('majority_gerrymandered.jpg', dpi=600)
    print("Dem Seats After Majority Gerrymander = ", GMA.TotalDemSeats(), file=outFile)
    GMA.PickleCountry("Majority_Gerrymandered.pkl")  
    
#Pickle a country in which the half has been gerrymandered in favor of 
#Republicans.
def RecordHalfGerrymander():
    outFile = open("1st_half_gerrymander_record.txt", 'w')
    GMA = Country("Gerrymandria")   
    GMA.PrintDemographics()
    GMA.draw_state_grid(4, plt)
    plt.savefig('half_initial.jpg', dpi=1000)
    
    print("Initial Dem Seats = ", GMA.TotalDemSeats(), file=outFile)
    GMA.GerrymanderHalf()
    GMA.draw_state_grid(4, plt)
    plt.savefig('half_gerrymandered.jpg', dpi=600)
    print("Dem Seats After Half Gerrymander = ", GMA.TotalDemSeats(), file=outFile)
    GMA.PickleCountry("Half_Gerrymandered.pkl")    

#def TipBalance():
#    GMA = Country("Gerrymandria")   
#    GMA.PrintDemographics()
#    GMA.draw_state_grid(4, plt)
#    plt.savefig('initial.jpg', dpi=600)
#    
#    print("Initial Dem Seats = ", GMA.TotalDemSeats(), file=outFile)
#    GMA.state_list[0] = GMA.SimulatedAnnealing(GMA.state_list[i])
#    GMA.draw_state_grid(4, plt)
#    plt.savefig('majority_gerrymandered.jpg', dpi=600)
#    print("Dem Seats After Majority Gerrymander = ", GMA.TotalDemSeats(), file=outFile)
#    GMA.PickleCountry("Majority_Gerrymandered.pkl")    


#From majority gerrymander, progressively gerrymander the rest in the same
#direction, checking to see whether Wang's effects test is triggered.
def ProgressiveGerrymanderFromMajority():
    inFile = open("Majority_Gerrymandered.pkl", 'rb')
    GMA = pickle.load(inFile)
    outFile = open("gerrymander_record.txt", 'w')


    #Now progressively gerrymander the remaining states.
    for i in range(len(GMA.state_list)):
        if GMA.state_list[i].name in "ABCDEFG":
            print("Total Dem Seats Before = ", GMA.TotalDemSeats(), file=outFile)
            print("State Name = ", GMA.state_list[i].name)
            print("State Name = ", GMA.state_list[i].name, file = outFile)
            p_before = GMA.EffectsTest(GMA.state_list[i])
            mm_before = GMA.state_list[i].MeanMedian()
            print("p_before = ", p_before, file = outFile)
            print("mm_before = ", mm_before, file = outFile)

            #Gerrymander in favor of Republicans
            GMA.state_list[i] = GMA.SimulatedAnnealingRep(GMA.state_list[i])
            
            print("Total Dem Seats After = ", GMA.TotalDemSeats(), file=outFile)
            p_after = GMA.EffectsTest(GMA.state_list[i])
            mm_after = GMA.state_list[i].MeanMedian()
            print("p_after = ", p_after, file = outFile)
            print("mm_after = ", mm_after, file = outFile)
            GMA.draw_state_grid(4, plt)
            plt.savefig(str(GMA.state_list[i].name) + '.jpg', dpi=600)
            
    print("Final Dem Seats = ", GMA.TotalDemSeats(), file=outFile)
    GMA.draw_state_grid(4, plt)
    outFile.close()
    

#From half gerrymander, progressively gerrymander the rest in the same
#direction, checking to see whether Wang's effects test is triggered.
def ProgressiveGerrymanderFromHalf():
    inFile = open("Half_Gerrymandered.pkl", 'rb')
    GMA = pickle.load(inFile)
    outFile = open("half_gerrymander_record.txt", 'w')


    #Now progressively gerrymander the remaining states.
    for i in range(len(GMA.state_list)):
        if GMA.state_list[i].name in "ABCDEFGH":
            print("Total Dem Seats Before = ", GMA.TotalDemSeats(), file=outFile)
            print("State Name = ", GMA.state_list[i].name)
            print("State Name = ", GMA.state_list[i].name, file = outFile)
            p_before = GMA.EffectsTest(GMA.state_list[i])
            mm_before = GMA.state_list[i].MeanMedian()
            print("p_before = ", p_before, file = outFile)
            print("mm_before = ", mm_before, file = outFile)

            #Gerrymander in favor of Republicans
            GMA.state_list[i] = GMA.SimulatedAnnealingRep(GMA.state_list[i])
            
            print("Total Dem Seats After = ", GMA.TotalDemSeats(), file=outFile)
            p_after = GMA.EffectsTest(GMA.state_list[i])
            mm_after = GMA.state_list[i].MeanMedian()
            print("p_after = ", p_after, file = outFile)
            print("mm_after = ", mm_after, file = outFile)
            GMA.draw_state_grid(4, plt)
            plt.savefig(str(GMA.state_list[i].name) + '_half.jpg', dpi=600)
            
    print("Final Dem Seats = ", GMA.TotalDemSeats(), file=outFile)
    GMA.draw_state_grid(4, plt)
    outFile.close()
    
#Create a country and gerrymander a single state.
def DemonstrateGerrymandering(contiguous = False):
    GMA = Country("Gerrymandria")   
    GMA.PrintDemographics()
    GMA.state_list[0].plot_state(plt.subplot())    
    plt.savefig('initial.jpg', dpi=600)
    for dist in GMA.state_list[0].districts:
        print(dist.name, dist.dems, dist.reps)
    print("Initial Dem Seats = ", GMA.state_list[0].MaxDemFitness())

    GMA.state_list[0] = GMA.SimulatedAnnealingDem(GMA.state_list[0], contiguous = True)
    plt.clf()
    GMA.state_list[0].plot_state(plt.subplot())    
    plt.savefig('GerrymanderedStateA.jpg', dpi=600)
    for dist in GMA.state_list[0].districts:
        print(dist.name, dist.dems, dist.reps)
    print("Dem Seats After Gerrymander = ", GMA.state_list[0].MaxDemFitness())
    plt.clf()
    GMA.EffectsTest(GMA.state_list[0])
    GMA.state_list[0].plot_state(plt.subplot())
    
#Illustrate how swapping of census blocks works.
def SingleSwap():
    GMA = Country("Gerrymandria")   
    GMA.PrintDemographics()
    GMA.state_list[0].plot_state(plt.subplot())    
    plt.savefig('BeforeSwap.jpg', dpi=600)
    for dist in GMA.state_list[0].districts:
        print(dist.name, dist.dems, dist.reps)
#    print("Initial Dem Seats = ", GMA.state_list[0].MaxDemFitness())

    GMA.state_list[0].DoSwaps(1)
    plt.clf()
    GMA.state_list[0].plot_state(plt.subplot())    
    plt.savefig('AfterSwap.jpg', dpi=600)
    for dist in GMA.state_list[0].districts:
        print(dist.name, dist.dems, dist.reps)
#    print("Dem Seats After Gerrymander = ", GMA.state_list[0].MaxDemFitness())



#RecordMajorityGerrymander()  
#RecordHalfGerrymander() 
#ProgressiveGerrymanderFromHalf()
#DemonstrateGerrymandering()
#SingleSwap()

DemonstrateGerrymandering()

#GMA.state_list[0] = GMA.SimulatedAnnealing(GMA.state_list[0], threshold = 0.9)
#GMA.state_list[0] = GMA.SimulatedAnnealing(GMA.state_list[0], threshold = 0.9)
#state = GMA.state_list[0]
#GMA.EffectsTest(state)
#state.plot_state(plt.subplot())
#for dist in state.districts:
#    print(dist.name, dist.dems, dist.reps)






#state.plot_state(plt.subplot())
#plt.savefig('once_gerrymandered.svg')  
#plt.savefig('state_' + state.name + '_gerrymandered.jpg', dpi=1000)
#GerrymanderMajority()    

#plt.savefig('majority_gerrymander.svg')
#plt.savefig('majority_gerrymander.jpg', dpi=300)
#PickleMajorityGerrymander()
       
          
          
          
          


