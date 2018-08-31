from __future__ import print_function

import sys
sys.path.append('../')

from include_lite import *

class SimpleDistrict:
    def __init__(self, code, ratio):
        self.__code = code
        self.__ratio = ratio

    def get_dem_ratio(self):
        return self.__ratio

    def set_dem_ratio(self, r):
        self.__ratio = r
    
    def get_code(self):
        return self.__code

    def get_state(self):
        return self.__code[:2]

def sd_check_sanity(arr):
    assert len(arr) == 435
    for a in arr:
        assert a.get_dem_ratio() < 1
        assert a.get_dem_ratio() > 0
    assert len(set([a.get_state() for a in arr])) == 50

def get_state_list(sd_arr):
    ret = list(set([a.get_state() for a in sd_arr]))
    ret.sort()
    return ret

def get_state(sd_arr, state_name):
    return [a for a in sd_arr if a.get_state() == state_name]
    
def state_dem_seats(sd_arr):
    return sum([1 for sd in sd_arr if sd.get_dem_ratio() > .5])

def state_dem_ratio(sd_arr):
    return avg([sd.get_dem_ratio() for sd in sd_arr])

        
def get_state_dict(dist_arr):    
    state_names = get_state_list(dist_arr)
    state_all = {}
    for name in state_names:
        state_all[name] = get_state(dist_arr, name)
    return state_names, state_all
