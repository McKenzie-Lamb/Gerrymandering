# -*- coding: utf-8 -*-
"""
Created on Tue Jun 13 11:08:38 2017

@author: mckenzielamb
"""

from shapely.geometry import Polygon

class CBlock:
    def __init__(self, dems, reps, shape):
        self.dems = dems
        self.reps = reps
        self.shape

class District(object):
    def __init__(self, name, cblocks):
        self.name = name
        self.total = total
        self.dem_vote = dem_vote
        self.rep_vote = rep_vote
        self.other_vote = other_vote
        self.winner = winner
        self.dem_share = dem_share
        self.rep_share = rep_share
        self.cblocks = cblocks
        self.shape = shape

class State:
    def __init__(self, districts, all_cblocks):
        self.districts = districts
        self.all_cblocks = all_cblocks