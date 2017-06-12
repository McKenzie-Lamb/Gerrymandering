# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import random
import csv
import collections
import statistics
class District(object):
    def __init__(self, name, total, dem_vote, rep_vote, other_vote, winner, dem_share, rep_share, pres_dem, pres_rep):
        self.name = name
        self.total = total
        self.dem_vote = dem_vote
        self.rep_vote = rep_vote
        self.other_vote = other_vote
        self.winner = winner
        self.dem_share = dem_share
        self.rep_share = rep_share
        self.pres_dem = pres_dem
        self.pres_rep = pres_rep
        
def remove_comma(string):   #remove comma in 4+ digit numbers and %s from data in cvs file 
    list_number = []
    for i in range(len(string)):
        if string[i] != ',' and string[i] != '%':
            list_number.append(string[i])
    number = ''.join(list_number)       
    return number

def state_dictionary(): #creates dictionary w/ state as key & number of districts as value
    data_file = open("2014_House_Data_Simplified.csv", 'r')
    data_dict_reader = csv.DictReader(data_file)
    count_dist = collections.Counter([row['Code'][:2] for row in data_dict_reader])
    return (count_dist)

def demographic_breakdown(state = "WI"):    #find percentages of Democrats&Republicans in a given state
    total_dem = 0
    total_rep = 0
    total_pop = 0
    for i in range(len(All_district)):
        if All_district[i].name[:2] == state:   #look at only districts in given state
            total_dem += All_district[i].dem_vote    #keep running total of votes for Democrats in given state
            total_rep += All_district[i].rep_vote    #keep running total of votes for Republicans in given state
            total_pop += All_district[i].total       #keep running total of all votes cast in given state
    total_percent_dem = total_dem / total_pop        #percent of votes cast for Democrat in given state
    total_percent_rep = total_rep / total_pop        #percent of votes cast for Republican in given state                                   
    return total_percent_dem, total_percent_rep


def simulation(New_list, number_district, number_samples = 100000):  #generates sample lists of random districts w/ same demographics as given state
    test_list  = []
    fail_count = 0
    extreme = 0
    print ('Number of districts: ', number_district)
    while len(test_list) < number_samples:
        simulated_set = random.sample(New_list, number_district) #generates list of random districts
        if abs(sum([dist.dem_vote for dist in simulated_set])/ sum([dist.total for dist in simulated_set]) 
        - total_percent_dem) <= 0.01:    #allow for margin of error of 1% for the demographic breakdown of the simualated set
            total_dem_seat = 0
            for dist in simulated_set:
                if dist.winner == "D":
                    total_dem_seat += 1
            if total_dem_seat <= current_dem_seat:
                extreme += 1
            test_list.append(total_dem_seat)
        else: 
            fail_count += 1
    #print (fail_count)
    #print (test_list)
    p_value = extreme / number_samples
    return (test_list, p_value)
state = input('Insert the abbreviation of the state: ', )
count_dist = state_dictionary()
number_district = count_dist.get(state)
All_district = []
with open('2014_House_Data_Simplified.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        All_district.append(District(row['Code'],
                                     int(remove_comma(row['Total'])),
                                     int(remove_comma(row['Dem'])), 
                                     int(remove_comma(row['Rep'])), 
                                     int(remove_comma(row['Other'])),
                                     row['Winner'],
                                     float(remove_comma(row['Dem_share'])), 
                                     float(remove_comma(row['Rep_share'])),
                                     float(remove_comma(row['Obama'])),
                                     float(remove_comma(row['Romney']))))

for dist in All_district:       #for uncontested districts, use information from 2012 presidential election instead
    if dist.dem_share == 0 and dist.rep_share == 0 and dist.other_vote == 0:
        dist.dem_share = dist.pres_dem/(dist.pres_dem + dist.pres_rep)
        dist.rep_share = dist.pres_rep/(dist.pres.dem + dist.pres_rep)


#print (demographic_breakdown())

total_percent_dem = demographic_breakdown()[0]
total_percent_rep = demographic_breakdown()[1]
New_list = []
current_dem_seat = 0
for dist in All_district:
    if dist.name[:2] != state:   
        New_list.append(dist) 
for dist in All_district:
    if dist.name[:2] == state and dist.winner == "D":
        current_dem_seat += 1
number_samples = 100000            
test_list, p_value = simulation(New_list, number_district, number_samples)
mean_test = sum([n for n in test_list])/number_samples #if number_sample changed in simulation(), change here as well
print ('Current democratic seats: ', current_dem_seat)
print ('Mean: ', mean_test)
sd = statistics.stdev(n for n in test_list)
print ('p_value: ', p_value)
print ('standard deviation: ', sd)



       
    
        