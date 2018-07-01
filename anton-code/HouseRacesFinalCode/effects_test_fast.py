from __future__ import print_function

import utils

def generate_many_samples(conf):
    """ Generates a collection of samples for the Effects Test

    Input:

    conf.ambient_districts (list of floats) -- list of ambient districts from which the sample is taken,
        each element is the ratio of democratic votes in that district
        (to conform with the Effects Test make sure to exclude the districts corresponding to the sampled state)
    conf.state_sz -- size of each sample (should be at least 2)
    conf.target (float) -- (see below)
    conf.margin (float) -- each generated sample should have ratio of democratic votes within the margin of target
    conf.max_attempts -- maximum number of attempts to find a sample
    conf.max_samples -- stop if we find this many samples

    Output:

    result.seat_prob_dist (list of floats) -- probability distribution for the Effects Test
    result.success_count -- number of generated samples
    result.tries -- number of attempts to generate a sample
    result.all_samples -- list of all the generated samples (see fn. generate_one_sample for more information)
    """
    
    # counts total weight of samples by number of democratic seats
    # example: seat_prob_dist[3] is the sum of weights of samples that have 3 democratic seats
    seat_prob_dist = [0.0]*(conf.state_sz+1)
    
    success_count = 0 # number of successfully computed samples so far

    all_samples = [] # keep track of all the generated samples
    
    for i in range(conf.max_attempts):
        sample_info = generate_one_sample(conf) # attempt to generate a sample
        
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
    

def generate_one_sample(conf):
    """ Generates a one samples for the Effects Test

    Input:

    conf.ambient_districts (list of floats) -- list of ambient districts from which the sample is taken,
        each element is the ratio of democratic votes in that district
        (to conform with the Effects Test make sure to exclude the districts corresponding to the sampled state)
    conf.state_sz -- size of each sample
    conf.target (float) -- (see below)
    conf.margin (float) -- each generated sample should have ratio of democratic votes within the margin of target

    Output:

    Output is None if the sample generation is unsuccessfull
    If the generation is successfull then the output is:

    sample_info.weight (float) -- weight of the generated sample
    sample_info.dem_seats -- number of democratic seats in the generated sample
    sample_info.sample_inx (list of indices) -- indices of the districts composing the generated sample
    """
    
    # indices of the available ambient districts
    # this list starts with everything and will shrink as we are constructing our sample
    ambient_districts_inx = list(range(len(conf.ambient_districts)))

    sample_inx = []   # constructed sample so far (stores indices of districts in the sample)
    sample_meta = []  # meta data for each of the picks of the sample
    
    assert conf.state_sz > 1 # this algorithm only makes sense if there is more than one district in the state

    # we construct the sample one distict at a time
    for i in range(conf.state_sz):
        # our picking algorithm is different for first and last picks
        # see implementations below
        if i == 0:
            make_pick_fn = _make_first_pick
        elif i < conf.state_sz - 1:
            make_pick_fn = _make_middle_pick
        else:
            make_pick_fn = _make_last_pick

        can_continue = make_pick_fn(sample_inx, sample_meta, ambient_districts_inx, conf)
            
        if not can_continue:
            return None     # failed to generate a sample

    sample_ratios = [conf.ambient_districts[i] for i in sample_inx]
    sample_dem_ratio = utils.avg([conf.ambient_districts[i] for i in sample_inx])
    sample_dem_seats = sum([1 for r in sample_ratios if r > .5])

    # sanity check: generated sample should have valid ratio of democratic votes
    assert utils.within(sample_dem_ratio, conf.target, conf.margin)

    # sanity check: correct length of lists
    assert len(sample_inx) == len(sample_meta)
    assert len(sample_inx) == conf.state_sz

    # We are done computing the sample. It is not uniformly random, so we have to compute its weight.
    weight = _compute_sample_weight(sample_inx, sample_ratios, sample_meta)
    
    sample_info = dummy()
    sample_info.weight = weight
    sample_info.dem_seats = sample_dem_seats
    sample_info.sample_inx = sample_inx
    
    return result

    
def _make_first_pick(sample, sample_meta, ambient_districts_inx, conf):
    i = random.choice(ambient_districts_inx)
    ambient_districts_inx.remove(i)

    sample.append(i)

    sample_meta.append(None)

    return True

def _make_middle_pick(sample_inx, sample_meta, ambient_districts_inx, conf):
    meta = dummy()

    picks_remain = conf.state_sz - len(sample_inx)
    assert len(sample_inx) > 0
    assert picks_remain > 1

    smpl, vote_now, pop_now = get_sample_info(sample_inx, conf)
    ratio_now = float(vote_now)/pop_now
    
    dist_ratios = [conf.ambient_districts[i][0] for i in ambient_districts_inx]
    dist_pops = [conf.ambient_districts[i][1] for i in ambient_districts_inx]
    
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
    
    lt_pool = [i for i in ambient_districts_inx if not lt_filter_fn(conf.ambient_districts[i])]
    ht_pool = [i for i in ambient_districts_inx if not ht_filter_fn(conf.ambient_districts[i])]

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

def _make_last_pick(sample_inx, sample_meta, ambient_districts_inx, conf):
    picks_remain = conf.state_sz - len(sample_inx)
    assert picks_remain == 1

    smpl, vote_now, pop_now = get_sample_info(sample_inx, conf)
    
    pool = []

    for i in ambient_districts_inx:
        rt, pop = conf.ambient_districts[i]
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
