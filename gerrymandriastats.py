# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 14:30:38 2017

@author: wr
"""

from gerrymandriastates import State,District,CBlock,draw_state_grid
import random
import statistics
import collections
import pickle
          
def Gerrymandria_demographic(state_set):                            #This function will give us the demographic breakdown of Gerrymandria
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

def demographic_breakdown(state,All_district):
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

       
def simulation (new_list, number_district, total_percent_dems, number_samples):
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

def calculate_p_value (sets,current_dem_seat,mean,number_samples):
    extreme = 0
    if current_dem_seat < mean:
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
          
def make_district_list(state_set):
    All_district = []
    for state in state_set:
         for district in state.districts:
              All_district.append(district)                   #A list of all district objects in Gerrymandria
    return All_district

def print_demographics(state_set):    
    print ("Overall: ",Gerrymandria_demographic(state_set))           #The results are 0.4978865879685357, 0.5021134120314642 
    districts = make_district_list(state_set)
    for state in state_set:
        print (state,":",demographic_breakdown(state.name,districts))       #Yay!! It worked!! 

def statistical_test(state,All_district,number_samples=1000):
    count_dist = collections.Counter([dist.name[:1] for dist in All_district])
    number_district = count_dist.get(state)     #number of districts in given state
    
    total_percent_dems,total_percent_reps = demographic_breakdown(state,All_district)

        
    new_list = []
    current_dem_seat = 0
    for dist in All_district:       #creates new list of districts to make up random 
        if dist.name[:1] != state:  #list of districts that discludes districts from given state   
            new_list.append(dist) 
    for dist in All_district:       #counts how many seats currently held in by democrats in given state
        if dist.name[:1] == state and dist.winner == "D":
            current_dem_seat += 1  
    test_list = simulation(new_list, number_district, total_percent_dems, number_samples)
    mean_test = sum(test_list)/number_samples     
    sd = statistics.stdev(test_list)
    p_value = calculate_p_value(test_list,current_dem_seat,mean_test,number_samples)
    return current_dem_seat,mean_test,sd,p_value



def main():
    filename = input("Data file to read: ")
    with open(filename,"rb") as thefile:
        state_set = pickle.load(thefile)
        
        print_demographics(state_set)
        
        All_district = make_district_list(state_set)
        
        state = 'A'

        total_percent_dems,total_percent_reps = demographic_breakdown(state,All_district)

        current_dem_seat,mean_simulated_dem_seats,sd,p_value = statistical_test(state,All_district,1000)

        print ('Current democratic seats: ', current_dem_seat)
        print ('Percentage of democrats in the state: ', total_percent_dems)
        print ('Mean: ', mean_simulated_dem_seats)
        print ('p_value: ', p_value)
        print ('standard deviation: ', sd)
        import matplotlib.pyplot as plt
        draw_state_grid(state_set,4,plt)

if __name__ == "__main__":
    main()
