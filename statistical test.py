# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

class District(object):
    def __init__(self, dem_vote, rep_vote, other_vote):
        self.dem_vote = dem_vote
        self.rep_vote = rep_vote
        self.other_vote = other_vote
        if max(self.dem_vote, self.rep_vote, self.other_vote) == self.dem_vote:
            self.dem_seat = 1
            self.rep_seat = 0
            self.other_seat = 0
        elif max(self.dem_vote, self.rep_vote, self.other_vote) == self.rep_vote:
            self.dem_seat = 0
            self.rep_seat = 1
            self.other_seat = 0
        else: 
            self.dem_seat = 0
            self.rep_seat = 0
            self.other_seat = 1
District()
import random
number_district = 8
total_dem = 55
total_rep = 45
def simulation(number = 100):  
    simulated_set = random.sample(All_district, number_district)
    test_list  = []
    for i in range (number_district):
        if sum(simulated_set[i].dem_vote) = total_dem:
            total_dem_seat = sum(district[i].dem_seat)
            test_list.append()
def statistical_test(number = 100):
    for i in range(number):
        stat_test_list = []
        stat_test_list.append(simulation)   
        mean
        standard deviation 
            
        
    
        