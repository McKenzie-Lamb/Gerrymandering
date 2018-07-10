from __future__ import print_function

from include_lite import *

import wang_tests, my_serializer, simple_district, pvalue
import two_test_gerrymander

import json, os, time
import os.path as op

with open('./src/seat_limits.json', 'r') as f:
    dist_info = jsonobj.load(f).__dict__
    
with open('./src/optimal_reach_levels.json', 'r') as f:
    lvls = jsonobj.load(f).__dict__
    
states = sorted([k for k in dist_info])
#print (states, len(states))

# for s in states:
#     # print(s, lvls[s].best_level)
#     print(json.dumps(lvls[s], default = lambda o: o.__dict__, indent=2))
#     print(json.dumps(dist_info[s], default = lambda o: o.__dict__, indent=2))

def try_target_once(dem_ratio, total_seats, target_seats, repeats, do_print=False):
    is_close_race = within(dem_ratio, .50, .05)
    
    res, ratios = two_test_gerrymander.random_trial(dem_ratio, total_seats, target_seats)
    assert res == 'success'
    
    ratios = two_test_gerrymander.local_search_simple(ratios, repeats)

    if two_test_gerrymander.fitness(ratios, is_close_race) == 0:
        if do_print:
            print('*')

        # assert wang_tests.margin_ttest(ratios) != 'fail'

        # if is_close_race:
        #     assert wang_tests.mean_median_test(ratios) == 'pass'
        # else:
        #     assert wang_tests.levene_test(ratios, two_test_gerrymander.dist_arr_ratios) == 'pass'
        
        return 'success', ratios
    else:
        if do_print:
            print('0', end='')
        return 'fail', None
        
def TwoTestGetRange(state_name):
    # if dist_info[state_name].two_test_range is None:
    #     return [dist_info[state_name].dem_seats, dist_info[state_name].dem_seats]
    # else:
    return dist_info[state_name].two_test_range

def PrintTimeInfo(state_name, optimal_level, target_seats):
    sim_info = lvls[state_name]
    out = dummy()

    out.name = state_name
    out.level = optimal_level
    out.target = target_seats
    out.range = dist_info[state_name].two_test_range
    
    out.times = []
    for e in sim_info.endpoints:
        for r in e.run_results:
            if r.level == optimal_level:
                out.times.append(round(r.time_per_success))
                
    print (jsonobj.dumps(out))
    
def TwoTestGerrymanderTo_old(state_name, target_seats):
    l, h = TwoTestGetRange(state_name)
    assert l <= target_seats and target_seats <= h

    optimal_level = lvls[state_name].best_level

    state_info = dist_info[state_name]

    ut = UpdateTime(30)
    print_mode = False

    while True:
        is_successfull, ratios = try_target_once(state_info.dem_ratio, state_info.seats, target_seats, optimal_level, print_mode)

        if is_successfull == 'success':
            return ratios

        if not print_mode and ut.is_update_time():
            PrintTimeInfo(state_name, optimal_level, target_seats)
            print_mode = True

def TwoTestGerrymanderTo(state_name, state_dem_ratio, target_seats, max_tries, optimal_level = None, quiet = False):
    if optimal_level is None:
        optimal_level = lvls[state_name].best_level

    state_info = dist_info[state_name]

    ut = UpdateTime(30)
    print_mode = False

    for i in range(max_tries):
        is_successfull, ratios = try_target_once(state_dem_ratio, state_info.seats, target_seats, optimal_level, print_mode)

        if is_successfull == 'success':
            return sorted(ratios)

        if not print_mode and ut.is_update_time() and quiet == False:
            PrintTimeInfo(state_name, optimal_level, target_seats)
            print_mode = True
            

