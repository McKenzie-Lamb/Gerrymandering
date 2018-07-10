from __future__ import print_function

from include_lite import *

import wang_tests, my_serializer, simple_district

import json
import os.path as op
from collections import namedtuple

def random_trial(dem_ratio, total_seats, target_seats):

    assert dem_ratio <= 1
    assert dem_ratio >= 0
    assert target_seats >= 0
    assert target_seats <= total_seats
    
    opp_target_seats = total_seats - target_seats
    
    if (target_seats * .51)/total_seats > dem_ratio:
        return 'too many', None
    
    if (target_seats * 1.0 + opp_target_seats * .49)/total_seats < dem_ratio:
        return 'too few', None

    target_sum = total_seats * dem_ratio - target_seats * .51

    assert .49*total_seats >= target_sum

    ratios = [random.uniform(0, .49) for i in range(total_seats)]
    #print(sum(ratios), target_sum)
    if sum(ratios) > target_sum:
        mlt = target_sum/sum(ratios)
        assert mlt <= 1
        assert mlt >= 0
        ratios = [r * mlt for r in ratios]
    else:
        mlt = (total_seats*.49 - target_sum)/(total_seats*.49 - sum(ratios))
        assert mlt <= 1
        assert mlt >= 0
        ratios = [.49 - ((.49 - r) * mlt) for r in ratios]

    assert almost_equal(sum(ratios), target_sum)

    for i in range(total_seats):
        assert ratios[i] >= 0
        assert ratios[i] <= .49, (i, ratios[i])
        
    for i in range(target_seats):
        ratios[i] += .51

    for i in range(target_seats):
        assert ratios[i] >= .51
        assert ratios[i] <= 1.0, ratios[i]
        
    for i in range(target_seats, total_seats):
        assert ratios[i] >= 0
        assert ratios[i] <= .49

    assert almost_equal(avg(ratios), dem_ratio), (avg(ratios), dem_ratio)

    return 'success', ratios

    

with open('./src/districts_adj_code_simple.json', 'r') as f:
    data = json.load(f)

dist_arr = my_serializer.districts_from_json(data['sm_districts'])
dist_arr_ratios = [d.get_dem_ratio() for d in dist_arr]

def get_wang_trial(dem_ratio, total_seats, target_seats, max_tries):
    is_close_race = within(dem_ratio, .50, .05)
    for i in range(max_tries):
        res, ratios = random_trial(dem_ratio, total_seats, target_seats)
        if res != 'success':
            return res, None
        res = wang_tests.pass_all_tests(ratios, dist_arr_ratios, is_close_race)
        if res == True:
            return 'success', ratios
    return 'ran out of tries', None


def fitness(ratios, is_close_race):
    ((t1, s1), (t2, s2)) = wang_tests.pass_all_tests_full(ratios, dist_arr_ratios, is_close_race)

    ret = 0

    if not t1:
        ret += 1000 + abs(s1)
    if not t2:
        ret += 1000 + abs(s2)

    # if (ret == 0):
    #     assert wang_tests.margin_ttest(ratios) != 'fail'

    #     if is_close_race:
    #         assert wang_tests.mean_median_test(ratios) == 'pass'
    #     else:
    #         assert wang_tests.levene_test(ratios, dist_arr_ratios) == 'pass'
    

    return ret

def random_step(old_ratios, limits_low, limits_high):
    step = .01
    new_ratios = copy.copy(old_ratios)
    sz = len(old_ratios)

    for i in range(4):
        a = random.randrange(sz)
        b = random.randrange(sz)
        if a == b:
            continue
        if new_ratios[a] + step > limits_high[a]:
            continue
        if new_ratios[b] - step < limits_low[b]:
            continue
        
        new_ratios[a] += step
        new_ratios[b] -= step

    assert almost_equal(sum(old_ratios), sum(new_ratios))

    return new_ratios

def local_search_simple(old_ratios, repeats):
    is_close_race = within(avg(old_ratios), .50, .05)

    assert all([ (0 <= r and r <= .49) or (.51 <= r and r <= 1) for r in old_ratios])

    limits_low  = [ (0 if r <= .49 else .51) for r in old_ratios]
    limits_high = [ (.49 if r <= .49 else 1) for r in old_ratios]

    old_fitness = fitness(old_ratios, is_close_race)
    
    for i in range(repeats):
        new_ratios = random_step(old_ratios, limits_low, limits_high)
        new_fitness = fitness(new_ratios, is_close_race)

        if new_fitness == 0:
            res = wang_tests.pass_all_tests(new_ratios, dist_arr_ratios, is_close_race)
            assert res == True
            
            return new_ratios

        if new_fitness <= old_fitness:
            old_ratios = new_ratios
            old_fitness = new_fitness
            
    return old_ratios

def local_search_simple_test(dem_ratio, total_seats, target_seats):
    is_close_race = within(dem_ratio, .50, .05)
    
    res, ratios = random_trial(dem_ratio, total_seats, target_seats)
    assert res == 'success'
    
    for i in range(1000):
        
        assert almost_equal(avg(ratios), dem_ratio)
        assert len([r for r in ratios if r >= .51]) == target_seats
        print (i)
        print (wang_tests.pass_all_tests_full(ratios, dist_arr_ratios, is_close_race))
        print (fitness(ratios, is_close_race))
        
        ratios = local_search_simple(ratios, 100)
    

with open('./src/districts_adj_code_simple.json', 'r') as f:
    data = json.load(f)

dist_arr = my_serializer.districts_from_json(data['sm_districts'])

state_names, state_dict = simple_district.get_state_dict(dist_arr)

big_state_names = [name for name in state_names if len(state_dict[name]) >= 2]
# print (big_state_names)

def generate_new_file(path, name, state_dict):
    folder_prep(path)
    state = state_dict[name]
    
    d = dummy()
    d.name = name
    d.ratio = simple_district.state_dem_ratio(state)
    d.seats = len(state)
    print(d.name, d.seats)

    d.results = ['']*(d.seats+1)
    
    for i in range(1, d.seats):
        print(i, end=' ')
        d.results[i] = get_wang_trial(d.ratio, d.seats, i, max_tries=10000)[0]
    print()

    sc = [i for i in range(d.seats) if d.results[i] == 'success']
    if (len(sc) > 0):        
        min_suc = min(sc)
        max_suc = max(sc)
        d.rng = [min_suc, max_suc]
    else:
        d.rng = None
        
    print (d.rng)

    with open(path, 'w') as f:
        json.dump(d, f, default = lambda o: o.__dict__, indent=2)

path = 'intervals'

class jsonobj:
    def __init__(self, dct):
        # print ('SUP')
        for k in dct:
            setattr(self, k, dct[k])
            # print (k, dct[k])

msg = 'ran out of tries'

if __name__ == '__main__':
    for i in range(10000):
        for name in big_state_names:
            fpath = op.join(path, name + '.json')

            if not op.exists(fpath):
                generate_new_file(fpath, name, state_dict)
                continue

            with open(fpath, 'r') as f:
                d = json.load(f, object_hook=lambda d: jsonobj(d))

            if d.rng == None:
                generate_new_file(fpath, name, state_dict)
                continue

            print(d.name, d.seats, d.rng)

            while True:
                ext = True
                sc = [i for i in range(d.seats) if d.results[i] == 'success']
                min_suc = min(sc)
                max_suc = max(sc)
                for i in [min_suc-1, max_suc+1]:
                    if i <= 0 or i >= d.seats:
                        continue
                    print(i , end=' ')

                    res, ratios = random_trial(d.ratio, d.seats, i)

                    if ratios == None:
                        print ('limited')
                        continue

                    rt = local_search_simple(ratios, repeats=10000)

                    is_close_race = within(avg(rt), .50, .05)
                    res = wang_tests.pass_all_tests(rt, dist_arr_ratios, is_close_race)
                    if res:
                        d.results[i] = 'success'
                        ext = False
                        print ('success')
                    else:
                        print ('fail')
                if ext:
                    break

            sc = [i for i in range(d.seats) if d.results[i] == 'success']
            min_suc = min(sc)
            max_suc = max(sc)
            if d.rng != [min_suc, max_suc]:
                d.rng = [min_suc, max_suc]

                with open(fpath, 'w') as f:
                    json.dump(d, f, default = lambda o: o.__dict__, indent=2)

    # st = state_dict['TX']
    # st_ratios = [d.get_dem_ratio() for d in st]

    # print (simple_district.state_dem_seats(st), len(st), simple_district.state_dem_ratio(st))
    #pprint (st_ratios)


    # ratio = simple_district.state_dem_ratio(st)
    # seats = len(st)

    # local_search_simple_test(ratio, seats, 19)

    # tries = 10000

    # results = ['']*(seats+1)

    # for i in range(1, seats):
    #     results[i] = get_wang_trial(ratio, seats, i, max_tries=1000)[0]

    # for i in range(100):
    #     min_suc = min([i for i in range(seats) if results[i] == 'success'])
    #     max_suc = max([i for i in range(seats) if results[i] == 'success'])
    #     print ((min_suc, max_suc))
    #     for i in [min_suc-1, max_suc+1]:
    #         if i <= 0 or i >= seats:
    #             continue
    #         print(i , end=' ')
    #         res = get_wang_trial(ratio, seats, i, max_tries=tries)[0]
    #         print (res)
    #         results[i] = res


