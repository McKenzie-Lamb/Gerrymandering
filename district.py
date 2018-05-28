# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 11:17:04 2017

@author: mckenzielamb
"""
import random

class District:
    def __init__(self, dem_vote, rep_vote, other_vote):
        self.dem_vote = dem_vote
        self.rep_vote = rep_vote
        self.other_vote = other_vote
        self.total_vote = dem_vote + rep_vote + other_vote
        if self.dem_vote > self.rep_vote and self.dem_vote > self.other_vote:
            self.dem_seat = 1
            self.rep_seat = 0
            self.other_seat = 0
        elif self.rep_vote > self.dem_vote and self.rep_vote > self.other_vote:
            self.dem_seat = 0
            self.rep_seat = 1
            self.other_seat = 0
        elif self.other_vote > self.rep_vote and self.other_vote > self.dem_vote:
            self.dem_seat = 0
            self.rep_seat = 0
            self.other_seat = 1 

def GenerateRandomDists(num_dists = 10): #Assume no other votes.
    return [District(random.randint(0,100), random.randint(0,100), 0) for i in range(num_dists)]

def Efficiency_Gap(districts):
   r_waste = 0
   d_waste = 0
   for dist in districts:
       if dist.dem_seat == 1:
           d_waste += dist.dem_vote - 0.5 * dist.total_vote
           r_waste += dist.rep_vote
       elif dist.rep_seat == 1:
           d_waste += dist.dem_vote 
           r_waste += dist.rep_vote - 0.5 * dist.total_vote
       else:
            d_waste += dist.dem_vote 
            r_waste += dist.rep_vote
   print("d_waste - r_waste =", d_waste - r_waste)

districts = GenerateRandomDists()
for dist in districts:
    print(dist.dem_vote, dist.rep_vote, dist.other_vote, dist.dem_seat)
Efficiency_Gap(districts)

            
        
    
        