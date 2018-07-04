from __future__ import print_function

import utils

def generate_many_samples(all_ambient_districts, state_sz, ratio_target, ratio_margin, max_attempts, max_samples):
    """ Generates a collection of samples for the Effects Test

    Input:

    all_ambient_districts (list of floats) -- list of ambient districts from which the sample is taken,
        each element is the ratio of democratic votes in that district
        (to conform with the Effects Test make sure to exclude the districts corresponding to the sampled state)
    state_sz -- size of each sample (should be at least 2)
    ratio_target (float) -- (see below)
    ratio_margin (float) -- each generated sample should have ratio of democratic votes within the margin of target
    max_attempts -- maximum number of attempts to find a sample
    max_samples -- stop if we find this many samples

    Output:

    seat_prob_dist (list of floats) -- probability distribution for the Effects Test
    all_samples -- list of all the generated samples (see fn. generate_one_sample for more information)
    """
    
    # counts total weight of samples by number of democratic seats
    # example: seat_prob_dist[3] is the sum of weights of samples that have 3 democratic seats
    seat_prob_dist = [0.0]*(state_sz+1)
    
    success_count = 0 # number of successfully computed samples so far

    all_samples = [] # keep track of all the generated samples
    
    for i in range(max_attempts):
         # attempt to generate a sample
        sample_dem_seats, weight, sample_inx = generate_one_sample(
                                                        all_ambient_districts,
                                                        state_sz,
                                                        ratio_target,
                                                        ratio_margin)
        
        if sample_info is not None:
            seat_prob_dist[dem_seats] += weight # update distribution
            
            all_samples.append(sample_info)
            
            success_count += 1

            if success_count >= max_samples:
                break
    
    return seat_prob_dist, all_samples
    

def generate_one_sample(all_ambient_districts, state_sz, ratio_target, ratio_margin):
    """ Generates a one samples for the Effects Test 

    Input:

    all_ambient_districts (list of floats) -- list of ambient districts from which the sample is taken,
        each element is the ratio of democratic votes in that district
        (to conform with the Effects Test make sure to exclude the districts corresponding to the sampled state)
    state_sz -- size of each sample
    ratio_target (float) -- (see below)
    ratio_margin (float) -- each generated sample should have ratio of democratic votes within the margin of target

    Output:

    Output is None,None,None if the sample generation is unsuccessfull
    If the generation is successfull then the output is:

    dem_seats -- number of democratic seats in the generated sample
    weight (float) -- weight of the generated sample
    sample_inx (list of indices) -- indices of the districts composing the generated sample
    """
    
    # indices of the available ambient districts
    # this list starts with everything and will shrink as we are constructing our sample
    available_districts_inx = list(range(len(all_ambient_districts)))

    sample_inx = []   # constructed sample so far (stores indices of districts in the sample)
    sample_meta = []  # meta data for each of the picks of the sample
    
    assert state_sz > 1 # this algorithm only makes sense if there is more than one district in the state

    # we construct the sample one distict at a time
    for i in range(state_sz):
        # our picking algorithm is different for first and last picks
        # see implementations below
        if i == 0:
            make_pick_fn = _make_first_pick
        elif i < state_sz - 1:
            make_pick_fn = _make_middle_pick
        else:
            make_pick_fn = _make_last_pick

        pick_index, pick_meta_info = make_pick_fn(
                                            available_districts_inx,
                                            all_ambient_districts,
                                            sample_inx,
                                            state_sz,
                                            ratio_target,
                                            ratio_margin)

        if pick_index is None:
            return None,None,None     # cannot make a pick, we have failed to generate a sample
        
        sample_inx.append(pick_index)      # add pick to our sample
        sample_meta.append(pick_meta_info) # add meta information
        
        available_districts_inx.remove(pick_index) # we cannot pick one district more than once
            

    sample_ratios = [all_ambient_districts[i] for i in sample_inx]
    sample_dem_ratio = utils.avg(sample_ratios)
    sample_dem_seats = sum([1 for r in sample_ratios if r > .5])

    # sanity check: generated sample should have valid ratio of democratic votes
    assert utils.within(sample_dem_ratio, ratio_target, ratio_margin)

    # sanity check: correct length of lists
    assert len(sample_inx) == len(sample_meta)
    assert len(sample_inx) == state_sz

    # We are done computing the sample. It is not uniformly random, so we have to compute its weight.
    weight = _compute_sample_weight(sample_inx, sample_ratios, sample_meta)
    
    return sample_dem_seats, weight, sample_inx

# first pick is just made randomly
def _make_first_pick(available_districts_inx, all_ambient_districts, sample_inx, state_sz, ratio_target, ratio_margin):
    pick_index = random.choice(available_districts_inx)
    pick_meta_info = None

    return pick_index, pick_meta_info

def _make_middle_pick(sample_inx, sample_meta, available_districts_inx, conf):
    meta = dummy()

    picks_remain = conf.state_sz - len(sample_inx)
    assert len(sample_inx) > 0
    assert picks_remain > 1

    smpl, vote_now, pop_now = get_sample_info(sample_inx, conf)
    ratio_now = float(vote_now)/pop_now
    
    dist_ratios = [conf.all_ambient_districts[i][0] for i in available_districts_inx]
    dist_pops = [conf.all_ambient_districts[i][1] for i in available_districts_inx]
    
    min_pop = min(dist_pops)
    max_pop = max(dist_pops)

    if ratio_now > conf.ratio_target - conf.ratio_margin:
        lt_pop_level = min_pop
    else:
        lt_pop_level = max_pop
        
    if ratio_now < conf.ratio_target + conf.ratio_margin:
        ht_pop_level = min_pop
    else:
        ht_pop_level = max_pop

    lt = threshold(vote_now, pop_now, picks_remain, lt_pop_level, conf.ratio_target - conf.ratio_margin)
    ht = threshold(vote_now, pop_now, picks_remain, ht_pop_level, conf.ratio_target + conf.ratio_margin)

    lt_filter_fn = lambda dist: dist[0] <= lt
    ht_filter_fn = lambda dist: dist[0] >= ht
    
    lt_pool = [i for i in available_districts_inx if not lt_filter_fn(conf.all_ambient_districts[i])]
    ht_pool = [i for i in available_districts_inx if not ht_filter_fn(conf.all_ambient_districts[i])]

    lt_filtered_num = len(available_districts_inx) - len(lt_pool)
    ht_filtered_num = len(available_districts_inx) - len(ht_pool)
    
    if lt_filtered_num < picks_remain:
        lt_filter_fn = lambda _: False
        lt_pool = available_districts_inx
        
    if ht_filtered_num < picks_remain:
        ht_filter_fn = lambda _: False
        ht_pool = available_districts_inx

    if len(lt_pool) < len(ht_pool):
        pool = lt_pool
        meta.filter_fn = lt_filter_fn
    else:
        pool = ht_pool
        meta.filter_fn = ht_filter_fn
        
    meta.ratio = float(len(pool))/len(available_districts_inx)

    if len(pool) == 0:
        return False
    
    i = random.choice(pool)
    available_districts_inx.remove(i)

    sample_inx.append(i)
    sample_meta.append(meta)

    return True

# look over all the possible last picks and choose a random one that results in a valid ratio
# (that is a ratio that is within margin of the target)
def _make_last_pick(available_districts_inx, all_ambient_districts, sample_inx, state_sz, ratio_target, ratio_margin):
    picks_remain = state_sz - len(sample_inx)
    assert picks_remain == 1 # this picking algorithm doesn't make sense if the pick is not last

    sample_ratios = [all_ambient_districts[i] for i in sample_inx] # democratic vote ratios of districts picked so far 
    sample_dem_ratio_sum = sum(sample_ratios)  # sum of all these ratios
    
    pool = [] # valid last picks

    for i in available_districts_inx: # check all remaining districts one by one to see which are valid
        pick_dem_ratio = all_ambient_districts[i] # ratio of the last pick
        final_dem_ratio = float(sample_dem_ratio_sum + pick_dem_ratio)/state_sz # ratio of the sample with the last pick
        
        if within(final_ratio, conf.ratio_target, conf.ratio_margin): # valid if close to the target
            pool.append(i)
            
    if len(pool) == 0: # no picks resulted in a valid sample
        return None, None 

    pick_index = random.choice(pool) # pick random valid last pick
    
    pick_meta_info = dummy()
    pick_meta_info.ratio = float(len(pool))/len(available_districts_inx) # proportion of valid picks

    return pick_index, pick_meta_info


# Compute the weight of a generated sample
def _compute_sample_weight(sample_inx, sample_ratios, sample_meta):
    total_weight = 1.0

    # total weight will be the product of individual weights for each pick

    # the weight for the first pick is 1 as it is completely random
    
    # next, we compute weights for all the picks except the last one
    for pos in range(1, len(sample_inx) - 1):
        
        affected_count = len(sample_inx) - pos # number of picks after this one
    
        filtered_count = 0 # how many of those picks would have been excluded using the filtering function
        
        for i in range(pos, len(sample_inx)):
            if i == pos:
                # sanity check: pick cannot filter itself out
                assert not sample_meta[pos].filter_fn(sample_ratios[i])

            if sample_meta[pos].filter_fn(sample_ratios[i]): 
                filtered_count += 1   # i'th pick is excluded using the filtering function of pos'th pick

        # adjustment_factor accounts for the effect on probability caused by
        # us excluding all the samples where all the picks would have been filtered out
        adjustment_factor = sample_meta[pos].ratio
        
        # combinatorics_factor accounts for the effect on probability caused by
        # picking unfiltered district first, instead of later on
        combinatorics_factor = float(affected_count) / (affected_count - filtered_count)
        
        # weight for this pick is the product of these two factors
        total_weight *= combinatorics_factor * adjustment_factor

    # finally the weight for the last pick is just the ratio of districts
    # that couldn't have been picked last without going outside the margin
    total_weight *= sample_meta[-1].ratio

    return total_weight
