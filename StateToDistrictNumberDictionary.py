# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 11:47:03 2017

@author: mckenzielamb
"""
from collections import Counter
import csv

def CreateDictionary():
    with open("2014_House_Data_Simplified.csv", 'r') as csv_file:
        data = csv.DictReader(csv_file) 
        dist_counter = Counter([row['Code'][:2] for row in data])
    print(dist_counter.most_common(52))
    
CreateDictionary()
         

        
