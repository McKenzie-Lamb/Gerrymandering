from __future__ import print_function

import my_utils

def generate_smart(conf):
    """ Generates a collection of samples for the Effects Test

    Input:

    conf.districts (list of floats) -- list of ambient districts from which the sample is taken,
        each element is the ratio of democratic votes in that district
        (to conform with the Effects Test make sure to exclude the districts corresponding to the sampled state)
    conf.state_sz -- size of each sample
    conf.target (float) -- (see below)
    conf.margin (float) -- each generated sample should have ratio of democratic votes within the margin of target
    conf.max_attempts -- maximum number of attempts to find a sample
    conf.max_samples -- stop if we find this many samples

    Output:

    result.seat_prob_dist (list of floats) -- probability distribution for the Effects Test
    result.success_count -- number of generated samples
    result.tries -- number of attempts to generate a sample
    result.all_samples -- list of all the generated samples (see fn. generate_smart_one for more information)
    """
    
    # counts total weight of samples by number of democratic seats
    # example: seat_prob_dist[3] is the sum of weights of samples that have 3 democratic seats
    seat_prob_dist = [0.0]*(conf.state_sz+1)
    
    success_count = 0 # number of successfully computed samples so far

    all_samples = [] # keep track of all the generated samples
    
    for i in range(conf.max_attempts):
        sample_info = generate_smart_one(conf) # attempt to generate a sample
        
        if sample_info is not None:
            seat_prob_dist[sample_info.dem_seats] += sample_info.weight # update distribution
            
            all_samples.append(sample_info)
            
            success_count += 1

            if success_count >= conf.max_samples:
                break

    result = dummy()
    result.all_samples = all_samples
    result.seat_prob_dist = seat_prob_dist
    result.success_count = success_count
    result.tries = i
    
    return result
    

def generate_smart_one(conf, ambient_districts_inx_, prepend):
    # indices 
    ambient_districts_inx = list(range(len(conf.districts)))
    ambient_districts_inx = copy.deepcopy(ambient_districts_inx_)

    sample_inx = copy.deepcopy(prepend)
    sample_meta = [None] * len(prepend)
    
    assert conf.state_sz > 1

    for i in range(len(prepend), conf.state_sz):
        if i == 0:
            fn = generate_smart_next_pick
        elif i < conf.state_sz - 1:
            fn = generate_smart_next_pick_cut
        else:
            fn = generate_smart_next_pick_last
            
        can_continue = fn(sample_inx, sample_meta, ambient_districts_inx, conf)
            
        if not can_continue:
            return None

    smpl, votes, pop = get_sample_info(sample_inx, conf)
    
    smpl_avg = float(votes)/pop

    assert within(smpl_avg, conf.target, conf.margin)
    
    smpl_st = sum([1 for rt, pop in smpl if rt > .5])

    assert len(sample_inx) == len(sample_meta)
    assert len(sample_inx) == conf.state_sz

    # print(sample_meta[3].ratio, sample_meta[3].is_low_cut)

    total_factor = weight_counter()
    
    for pos in range(1, len(sample_inx) - 1):
        if sample_meta[pos] is None or not hasattr(sample_meta[pos], 'filter_fn'):
            continue
        
        affected_count = len(sample_inx) - pos
        filtered_count = 0
        for i in range(pos, len(sample_inx)):
            if i == pos:
                assert not sample_meta[pos].filter_fn(smpl[i])

            if sample_meta[pos].filter_fn(smpl[i]):
                filtered_count += 1

        combinatorics_factor = float(affected_count) / (affected_count - filtered_count)
        adjustment_factor = sample_meta[pos].ratio

        total_factor.add(combinatorics_factor * adjustment_factor)

    total_factor.add(sample_meta[-1].ratio)
    
    return (sample_inx, smpl_st, total_factor)
 
def generate_smart_next_pick_last(sample_inx, sample_meta, ambient_districts_inx, conf):
    picks_remain = conf.state_sz - len(sample_inx)
    assert picks_remain == 1

    smpl, vote_now, pop_now = get_sample_info(sample_inx, conf)
    
    pool = []

    for i in ambient_districts_inx:
        rt, pop = conf.districts[i]
        vote_tot = vote_now + rt*pop
        pop_tot = pop_now + pop
        final_ratio = float(vote_tot)/pop_tot
        if within(final_ratio, conf.target, conf.margin):
            pool.append(i)
    if len(pool) == 0:
        return False

    meta = dummy()
    meta.ratio = float(len(pool))/len(ambient_districts_inx)
    
    i = random.choice(pool)
    ambient_districts_inx.remove(i)

    sample_inx.append(i)
    sample_meta.append(meta)

    return True

def generate_smart_next_pick_cut(sample_inx, sample_meta, ambient_districts_inx, conf):
    meta = dummy()

    picks_remain = conf.state_sz - len(sample_inx)
    assert len(sample_inx) > 0
    assert picks_remain > 1

    smpl, vote_now, pop_now = get_sample_info(sample_inx, conf)
    ratio_now = float(vote_now)/pop_now
    
    dist_ratios = [conf.districts[i][0] for i in ambient_districts_inx]
    dist_pops = [conf.districts[i][1] for i in ambient_districts_inx]
    
    min_pop = min(dist_pops)
    max_pop = max(dist_pops)

    if ratio_now > conf.target - conf.margin:
        lt_pop_level = min_pop
    else:
        lt_pop_level = max_pop
        
    if ratio_now < conf.target + conf.margin:
        ht_pop_level = min_pop
    else:
        ht_pop_level = max_pop

    lt = threshold(vote_now, pop_now, picks_remain, lt_pop_level, conf.target - conf.margin)
    ht = threshold(vote_now, pop_now, picks_remain, ht_pop_level, conf.target + conf.margin)

    lt_filter_fn = lambda dist: dist[0] <= lt
    ht_filter_fn = lambda dist: dist[0] >= ht
    
    lt_pool = [i for i in ambient_districts_inx if not lt_filter_fn(conf.districts[i])]
    ht_pool = [i for i in ambient_districts_inx if not ht_filter_fn(conf.districts[i])]

    lt_filtered_num = len(ambient_districts_inx) - len(lt_pool)
    ht_filtered_num = len(ambient_districts_inx) - len(ht_pool)
    
    if lt_filtered_num < picks_remain:
        lt_filter_fn = lambda _: False
        lt_pool = ambient_districts_inx
        
    if ht_filtered_num < picks_remain:
        ht_filter_fn = lambda _: False
        ht_pool = ambient_districts_inx

    if len(lt_pool) < len(ht_pool):
        pool = lt_pool
        meta.filter_fn = lt_filter_fn
    else:
        pool = ht_pool
        meta.filter_fn = ht_filter_fn
        
    meta.ratio = float(len(pool))/len(ambient_districts_inx)

    if len(pool) == 0:
        return False
    
    i = random.choice(pool)
    ambient_districts_inx.remove(i)

    sample_inx.append(i)
    sample_meta.append(meta)

    return True

def generate_smart_next_pick(sample, sample_meta, ambient_districts_inx, conf):
    i = random.choice(ambient_districts_inx)
    ambient_districts_inx.remove(i)

    sample.append(i)

    sample_meta.append(None)

    return True

def compute_error(arr1, arr2):
    assert len(arr1) == len(arr2)
    sz = len(arr1)
    
    n1 = sum(arr1)
    n2 = sum(arr2)

    if(n2 == 0):
        return 0

    errs = [0]*sz
    for i in range(sz):
        p1 = float(arr1[i])/n1
        p2 = float(arr2[i])/n2

        if p1 == 0:
            assert p2 == 0
        else:
            diff = abs(p1 - p2)
            SD = math.sqrt(p1*(1-p1)/n2)

            errs[i] = diff/SD

    return max(errs)

if __name__ == "__main__":
    conf = dummy()

    conf.country_sz = 30
    conf.state_sz = 5

    conf.district_ratios = [float(i)/(conf.country_sz-1) for i in range(conf.country_sz)]
    conf.district_pop = [random.uniform(5, 10) for i in range(conf.country_sz)]
    conf.districts = list(zip(conf.district_ratios, conf.district_pop))

    conf.target = .10
    conf.margin = .05

    conf.repeats = 1000
    conf.num_of_samples = conf.repeats
    conf.timed = True

    prepend = []

    rnd_repeats = 5
    seat_sz = conf.state_sz + 1

    # st_rn, time_rn = time_fn(generate_random, conf, prepend)
    # (_, cnt), time_sm = time_fn(generate_smart, conf, prepend)

    # print("random time per sample ", time_rn/sum(st_rn))
    # print("smart  time per sample ", time_sm/cnt)


    seat_prob_dist_all = generate_all(conf, prepend)
    actual_sr = success_rate_raw(seat_prob_dist_all, nCr(conf.country_sz - len(prepend), conf.state_sz - len(prepend)))
    print("complete, success rate", per_conv(actual_sr))

    seat_prob_dist_rnds = []
    for i in range(rnd_repeats):
        seat_prob_dist_rnds.append(generate_random(conf, prepend))
        # print(seat_prob_dist_rnds[-1])
        # print('.',end='')
    print()


    seat_prob_dist_rnd_sum = [sum(s[j] for s in seat_prob_dist_rnds) for j in range(seat_sz)]

    print("random, avg success rate", success_rate_err(seat_prob_dist_rnd_sum, conf.repeats*rnd_repeats, actual_sr))

    seat_prob_dist_rnd_errs = [round(compute_error(seat_prob_dist_all, d),1) for d in seat_prob_dist_rnds]
    print ("random errors", seat_prob_dist_rnd_errs)


    #fc = sum(seat_prob_dist_rnd)/sum(seat_prob_dist_all)
    #seat_prob_dist_all = [round(f*fc,1) for f in seat_prob_dist_all]

    # print(seat_prob_dist_all, "\n")

    ret = generate_smart(conf, prepend)

    seat_prob_dist_smt = ret.seat_prob_dist
    cnt = ret.success_count

    print("smart, simulated success rate", success_rate_err(seat_prob_dist_smt, conf.repeats, actual_sr))
    print("smart, actual success rate", success_rate([cnt], conf.repeats))
    print("error ", round(compute_error(seat_prob_dist_all, seat_prob_dist_smt),1))

    # fc = 1#sum(seat_prob_dist_rnd)/sum(seat_prob_dist_smt)
    # print([round(s*fc, 1) for s in seat_prob_dist_smt])
