from __future__ import print_function

from include_lite import *

import wang_tests

def is_close_fn(cut_conf, dem_ratio):
    low = cut_conf.close_race_low_cutoff
    high = cut_conf.close_race_high_cutoff

    return (low < dem_ratio) and (dem_ratio < high)

def random_trial(dem_ratio, total_seats, target_seats, cut_conf):
    low = cut_conf.safe_seat_low_cutoff
    high = cut_conf.safe_seat_high_cutoff
    
    assert dem_ratio <= 1
    assert dem_ratio >= 0
    assert target_seats >= 0
    assert target_seats <= total_seats

    assert 0 <= low
    assert low < high
    assert high <= 1

    dem_seats = target_seats
    rep_seats = total_seats - dem_seats

    dem_range = list(range(dem_seats))
    rep_range = list(range(dem_seats, total_seats))

    assert len(dem_range) == dem_seats
    assert len(rep_range) == rep_seats

    
    rep_seats = total_seats - dem_seats
    
    if (dem_seats * high + rep_seats * 0.0)/total_seats > dem_ratio:
        return 'too many', None
    
    if (dem_seats * 1.0 + rep_seats * low)/total_seats < dem_ratio:
        return 'too few', None

    target_sum = total_seats * dem_ratio - dem_seats * high

    ratios = [random.uniform(high, 1) for i in dem_range]
    ratios += [random.uniform(0, low) for i in rep_range]

    assert len(ratios) == total_seats

    target_sum = total_seats * dem_ratio
    
    if sum(ratios) > target_sum:
        target_sum_adj = target_sum - high * dem_seats

        for i in dem_range:
            ratios[i] -= high
        
        mlt = target_sum_adj/sum(ratios)
        
        assert mlt <= 1
        assert mlt >= 0
        
        ratios = [r * mlt for r in ratios]
        
        for i in dem_range:
            ratios[i] += high
    else:
        ratios = [1 - r for r in ratios]
        target_sum_adj = (total_seats - target_sum) - (1 - low) * rep_seats

        for i in rep_range:
            ratios[i] -= (1 - low)
        
        mlt = target_sum_adj/sum(ratios)
        
        assert mlt <= 1
        assert mlt >= 0
        
        ratios = [r * mlt for r in ratios]
        
        for i in rep_range:
            ratios[i] += (1 - low)
            
        ratios = [1 - r for r in ratios]

    assert almost_equal(sum(ratios), target_sum)

    for i in rep_range:
        assert ratios[i] >= 0
        assert ratios[i] <= low, (i, ratios[i])
        
    for i in dem_range:
        assert ratios[i] >= high, (i, ratios[i], high)
        assert ratios[i] <= 1.0, ratios[i]

    assert almost_equal(avg(ratios), dem_ratio), (avg(ratios), dem_ratio)

    return 'success', ratios

def random_search(dem_ratio, total_seats, target_seats, max_tries, cut_conf):
    is_close_race = is_close_fn(cut_conf, dem_ratio)
    for i in range(max_tries):
        res, ratios = random_trial(dem_ratio, total_seats, target_seats, cut_conf)
        if res != 'success':
            return res, None
        res = wang_tests.pass_all_tests(ratios, cut_conf.levene_ratios, is_close_race)
        if res == True:
            return 'success', ratios
    return 'ran out of tries', None

def fitness(ratios, levene_ratios, is_close_race):
    ((t1, s1), (t2, s2)) = wang_tests.pass_all_tests_full(ratios, levene_ratios, is_close_race)

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

def local_search_simple(old_ratios, repeats, cut_conf):
    is_close_race = is_close_fn(cut_conf, avg(old_ratios))
    
    low = cut_conf.safe_seat_low_cutoff
    high = cut_conf.safe_seat_high_cutoff

    assert all([ (0 <= r and r <= low) or (high <= r and r <= 1) for r in old_ratios])

    limits_low  = [ (0 if r <= low else high) for r in old_ratios]
    limits_high = [ (low if r <= low else 1) for r in old_ratios]

    old_fitness = fitness(old_ratios, cut_conf.levene_ratios, is_close_race)
    
    for i in range(repeats):
        new_ratios = random_step(old_ratios, limits_low, limits_high)
        new_fitness = fitness(new_ratios, cut_conf.levene_ratios, is_close_race)

        if new_fitness == 0:
            res = wang_tests.pass_all_tests(new_ratios, cut_conf.levene_ratios, is_close_race)
            assert res == True
            
            return new_ratios

        if new_fitness <= old_fitness:
            old_ratios = new_ratios
            old_fitness = new_fitness
            
    return old_ratios

def check_correctness(ratios, dem_ratio, total_seats, target_seats, cut_conf):
    assert len(ratios) == total_seats
    assert ratios == sorted(ratios)
    
    high = len([r for r in ratios if r >= cut_conf.safe_seat_high_cutoff])
    low = len([r for r in ratios if r <= cut_conf.safe_seat_low_cutoff])

    assert high == target_seats
    assert low == (total_seats - target_seats)

    assert almost_equal(dem_ratio, avg(ratios))
    
    is_close_race = is_close_fn(cut_conf, dem_ratio)
    assert fitness(ratios, cut_conf.levene_ratios, is_close_race) == 0
    
    assert wang_tests.margin_ttest(ratios) != 'fail'

    if is_close_race:
        assert wang_tests.mean_median_test(ratios) != 'fail'
    else:
        assert wang_tests.levene_test(ratios, cut_conf.levene_ratios) != 'fail'

def TwoTestCustomGerrymanderTo(dem_ratio, total_seats, target_seats, 

                               levene_ratios = None,
                               safe_seat_low_cutoff = .49,
                               safe_seat_high_cutoff = .51,
                               close_race_low_cutoff = .45,
                               close_race_high_cutoff = .55,
                               do_print = True,
                               max_time = 1000000,

                               first_batch_size = 100,
                               second_batch_size = 10,
                               batch_transfer_iteration = 0,
                               max_repeats_for_each = 10000,
                               repeats_at_a_time = 100

):
    assert safe_seat_low_cutoff < safe_seat_high_cutoff
    assert close_race_low_cutoff < close_race_high_cutoff

    cut_conf = dummy()
    cut_conf.safe_seat_low_cutoff = safe_seat_low_cutoff
    cut_conf.safe_seat_high_cutoff = safe_seat_high_cutoff
    cut_conf.close_race_low_cutoff = close_race_low_cutoff
    cut_conf.close_race_high_cutoff = close_race_high_cutoff
    cut_conf.levene_ratios = levene_ratios
    
    is_close_race = is_close_fn(cut_conf, dem_ratio)

    if not is_close_race:
        assert levene_ratios is not None

    max_repeats_for_each //= repeats_at_a_time

    give_up_time = UpdateTime(max_time)
    
    batch_full = [random_trial(dem_ratio, total_seats, target_seats, cut_conf) for i in range(first_batch_size)]
    assert all([res == 'success' for res, ratios in batch_full])
    
    batch = [ratios for res, ratios in batch_full]

    for j in range(max_repeats_for_each):
        for i in range(len(batch)):
            batch[i] = local_search_simple(batch[i], repeats_at_a_time, cut_conf)
            if fitness(batch[i], levene_ratios, is_close_race) == 0:
                ret = sorted(batch[i])
                check_correctness(ret, dem_ratio, total_seats, target_seats, cut_conf)
                return ret
            
        if give_up_time.is_update_time():
            if do_print:
                print("Ran out of time, giving up.")
            return None
            
        if j == batch_transfer_iteration:
            assert len(batch) == first_batch_size
            batch_fitness = [fitness(b, levene_ratios, is_close_race) for b in batch]
            pr = [(batch[i], batch_fitness[i]) for i in range(first_batch_size)]
            pr.sort(key = lambda a : a[1])
            pr = pr[:second_batch_size]
            batch = [b for b,f in pr]
            assert len(batch) == second_batch_size
    return None
