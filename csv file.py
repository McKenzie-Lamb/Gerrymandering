#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 14:53:52 2017

@author: trannguyenphuongngan
"""
class District(object):
    def __init__(self, name, total, dem_vote, rep_vote, other_vote, dem_share, rep_share):
        self.name = name
        self.total = total
        self.dem_vote = dem_vote
        self.rep_vote = rep_vote
        self.other_vote = other_vote
        self.dem_share = dem_share
        self.rep_share = rep_share
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
def remove_comma(string):
    list_number = []
    for i in range(len(string)):
        if string[i] != ',' and string[i] != '%':
            list_number.append(string[i])
    number = ''.join(list_number)       
    return number
import csv
All_district = []
with open('2014_House_Data_Simplified.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        All_district.append(District(row['Code'],
                                     int(remove_comma(row['Total'])),
                                     int(remove_comma(row['Dem'])), 
                                     int(remove_comma(row['Rep'])), 
                                     int(remove_comma(row['Other'])), 
                                     float(remove_comma(row['Dem_share'])), 
                                     float(remove_comma(row['Rep_share']))))
def demographic_breakdown(state = "WI"):
    total_dem = 0
    total_rep = 0
    total_pop = 0
    for i in range(len(All_district)):
        if All_district[i].name[:2] == state:
            total_dem += All_district[i].dem_vote
            total_rep += All_district[i].rep_vote
            total_pop += All_district[i].total 
    total_percent_dem = total_dem / total_pop
    total_percent_rep = total_rep / total_pop                                           
    return total_percent_dem*100, total_percent_rep*100
print (demographic_breakdown())

        