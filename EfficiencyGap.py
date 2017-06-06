# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 11:17:04 2017

@author: mckenzielamb
"""
import csv

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
        else: #self.other_vote > self.rep_vote and self.other_vote > self.dem_vote:
            self.dem_seat = 0
            self.rep_seat = 0
            self.other_seat = 1 

def EfficiencyGap(state = "WI"):
    with open("2014_House_Data_Simple.csv", 'r') as csv_file:
        data = csv.DictReader(csv_file)
        districts = []        
        for row in data:
            if row['Code'][:2] == state:
                districts.append(District(int(row['Dem'].replace(",", "")), 
                                          int(row['Rep'].replace(",", "")),
                                          int(row['Other'].replace(",", ""))))
        CalculateEfficiencyGap(districts)

def CalculateEfficiencyGap(districts):
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
   overall_total_vote = sum([dist.total_vote for dist in districts])            
   print("(d - r) / t =", (d_waste - r_waste) / overall_total_vote)

#Efficiency_Gap(districts)

EfficiencyGap(state = "MD")
            
        
    
        