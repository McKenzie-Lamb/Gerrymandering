#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 14:53:52 2017

@author: trannguyenphuongngan
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
def remove_comma(string):
    list_number = []
    for i in range(len(string)):
        if string[i] != ',' and string[i] != '%':
            list_number.append(string[i])
    number = ''.join(list_number)       
    return number
import csv
All_district = []
with open('2014 House Data (Simplified) - Sheet1.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        
        All_district.append(District(int(remove_comma(row['Dem'])), int(remove_comma(row['Rep'])), int(remove_comma(row['Other']))))
print (All_district[0].rep_seat)

        