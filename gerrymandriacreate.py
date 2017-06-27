# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 14:22:55 2017

@author: wr
"""

from gerrymandriastates import State,District,CBlock
import random
from shapely.geometry import Polygon
import pickle

def make_cblocks():   #create cblocks of one state  - cblocks are 1x1    
    cblock_array = []
    for i in range(8):
        row = []
        for j in range(8):
            dems = 101
            while dems < 0 or dems > 100:  #random demographics of political affiliation       
                dems = int(random.gauss(50, 10) + .5)
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
            dems += cblock_array[i][j].dems     #record number of democrats in district
            reps += cblock_array[i][j].reps     #record number of republicans in district
    if dems > reps:     #record district winner
        winner = "D"
    elif reps > dems:
        winner = "R"
    else:
        winner = "?"
    district = District(name, cblock_set, dems, reps, winner)
    return district

def make_state(name):   #make state - state is 8x8
    all_cblocks = make_cblocks()
    district_set = set()
    district_num = 1
    for i in range(0,8,4):
        for j in range(0,8,4):
            district = make_dist (i, i+4, j, j+4, "{0}-{1}".format(name, district_num), all_cblocks) #establish state districts w/ name and cblocks
            district_set.add(district)
            district_num += 1
    state = State(name, district_set, all_cblocks)
    return state 

def main():
    state_names = "ABCDEFGHIJKLMNOP"
    state_set = {make_state(name) for name in state_names}    #A list of all state objects in Gerrymandria
    filename = input("File in which to store data: ")
    with open(filename,"wb") as thefile:
        pickle.dump(state_set,thefile)

if __name__ == "__main__":
    main()