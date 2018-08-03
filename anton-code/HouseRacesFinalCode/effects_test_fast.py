import random

def generate_many_samples(ambient_districts, state_sz, ratio_target, ratio_margin, max_attempts, max_samples):
    """ Generates a collection of samples for the Effects Test

    Input:

    ambient_districts (list of floats) -- list of ambient districts from which the sample is taken,
        each element is the ratio of democratic votes in that district
        ** to conform with the Effects Test make sure to exclude the districts corresponding to the sampled state **
    state_sz -- size of each sample (should be at least 2)
    ratio_target (float) -- (see below)
    ratio_margin (float) -- each generated sample should have ratio of democratic votes within the margin of target
    max_attempts -- maximum number of attempts to find a sample
    max_samples -- stop if we find this many samples

    Output:

    seat_prob_dist (list of floats) -- probability distribution for the Effects Test
    all_samples -- list of all the generated samples (outputs of generate_one_sample, see function below for more information)
    """
    
    # counts total weight of samples by number of democratic seats
    # example: seat_prob_dist[3] is the sum of weights of samples that have 3 democratic seats
    seat_prob_dist = [0.0]*(state_sz+1)
    
    success_count = 0 # number of successfully computed samples so far

    all_samples = [] # keep track of all the generated samples
    
    for i in range(max_attempts):
         # attempt to generate a sample
        sample_dem_seats, weight, sample_inx = generate_one_sample(
                                                        ambient_districts,
                                                        state_sz,
                                                        ratio_target,
                                                        ratio_margin)
        
        if sample_dem_seats is not None:
            seat_prob_dist[sample_dem_seats] += weight # update distribution
            
            all_samples.append( (sample_dem_seats, weight, sample_inx) )
            
            success_count += 1

            if success_count >= max_samples:
                break
    
    return seat_prob_dist, all_samples
    

def generate_one_sample(ambient_districts, state_sz, ratio_target, ratio_margin):
    """ Generates one sample for the Effects Test 

    Input:

    ambient_districts (list of floats) -- list of ambient districts from which the sample is taken,
        each element is the ratio of democratic votes in that district
        (to conform with the Effects Test make sure to exclude the districts corresponding to the sampled state)
    state_sz -- size of the sample
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
    available_districts_inx = list(range(len(ambient_districts)))

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
            make_pick_fn = _make_selective_pick
        else:
            make_pick_fn = _make_last_pick

        pick_index, pick_meta_info = make_pick_fn(
                                            available_districts_inx,
                                            ambient_districts,
                                            sample_inx,
                                            state_sz,
                                            ratio_target,
                                            ratio_margin)

        if pick_index is None:
            return None,None,None     # cannot make a pick, we have failed to generate a sample
        
        sample_inx.append(pick_index)      # add pick to our sample
        sample_meta.append(pick_meta_info) # add meta information
        
        available_districts_inx.remove(pick_index) # we cannot pick one district more than once
            

    sample_ratios = [ambient_districts[i] for i in sample_inx]
    sample_dem_ratio = _average(sample_ratios)
    sample_dem_seats = sum([1 for r in sample_ratios if r > .5])

    # sanity check: generated sample should have valid ratio of democratic votes
    assert _within(sample_dem_ratio, ratio_target, ratio_margin)

    # sanity check: correct length of lists
    assert len(sample_inx) == len(sample_meta)
    assert len(sample_inx) == state_sz

    # We are done computing the sample. It is not uniformly random, so we have to compute its weight.
    weight = _compute_sample_weight(sample_inx, sample_ratios, sample_meta)
    
    return sample_dem_seats, weight, sample_inx

# first pick is just made randomly
def _make_first_pick(available_districts_inx, ambient_districts, sample_inx, state_sz, ratio_target, ratio_margin):
    pick_index = random.choice(available_districts_inx)
    pick_meta_info = None

    return pick_index, pick_meta_info

# algorithm for selective picking
def _make_selective_pick(available_districts_inx, ambient_districts, sample_inx, state_sz, ratio_target, ratio_margin):
    picks_remain = state_sz - len(sample_inx) # number of picks left to make

    sample_ratios = [ambient_districts[i] for i in sample_inx] # ratios of districts picked so far
    sample_dem_ratio_sum = sum(sample_ratios) # sum of these ratios

    # compute low and high thresholds
    low_threshold  = _compute_threshold(sample_dem_ratio_sum, picks_remain, state_sz, ratio_target - ratio_margin)
    high_threshold = _compute_threshold(sample_dem_ratio_sum, picks_remain, state_sz, ratio_target + ratio_margin)

    # functions to determine low-excluded and high-excluded districts
    low_filter_fn  = lambda district_ratio: district_ratio <= low_threshold
    high_filter_fn = lambda district_ratio: district_ratio >= high_threshold

    # pools of low-allowed and high-allowed districts (or, more precisely, district indices)
    low_pool  = [i for i in available_districts_inx if not low_filter_fn(ambient_districts[i])]
    high_pool = [i for i in available_districts_inx if not high_filter_fn(ambient_districts[i])]

    # how many districts were low-excluded? high-excluded?
    low_filtered_num  = len(available_districts_inx) - len(low_pool)
    high_filtered_num = len(available_districts_inx) - len(high_pool)

    # low threshold doesn't apply if we have to make more picks than the low-excluded districts
    # (since we are picking without replacement)
    if low_filtered_num < picks_remain:
        low_filter_fn = lambda _: False
        low_pool = available_districts_inx

    # similarly for high threshold
    if high_filtered_num < picks_remain:
        high_filter_fn = lambda _: False
        high_pool = available_districts_inx

    # pick the most restrictive exclusion
    if len(low_pool) < len(high_pool): # low exclusion is more restrictive
        final_pool = low_pool
        final_filter_fn = low_filter_fn
    else:                           # high exclusion is more restrictive
        final_pool = high_pool
        final_filter_fn = high_filter_fn
        
    if len(final_pool) == 0: # no picks resulted in a valid sample
        return None, None 

    pick_index = random.choice(final_pool) # pick random district from pool
    
    pick_meta_info = dummy()
    pick_meta_info.filter_fn = final_filter_fn

    # compute what proportion of districts were available to pick
    pick_meta_info.ratio = float(len(final_pool))/len(available_districts_inx)

    return pick_index, pick_meta_info

# look over all the possible last picks and choose a random one that results in a valid ratio
# (that is a ratio that is within margin of the target)
def _make_last_pick(available_districts_inx, ambient_districts, sample_inx, state_sz, ratio_target, ratio_margin):
    picks_remain = state_sz - len(sample_inx)
    assert picks_remain == 1 # this picking algorithm doesn't make sense if the pick is not last

    sample_ratios = [ambient_districts[i] for i in sample_inx] # democratic vote ratios of districts picked so far 
    sample_dem_ratio_sum = sum(sample_ratios)  # sum of all these ratios
    
    pool = [] # valid last picks

    for i in available_districts_inx: # check all remaining districts one by one to see which are valid
        pick_dem_ratio = ambient_districts[i] # ratio of the last pick
        final_dem_ratio = float(sample_dem_ratio_sum + pick_dem_ratio)/state_sz # ratio of the sample with the last pick
        
        if _within(final_dem_ratio, ratio_target, ratio_margin): # valid if close to the target
            pool.append(i)
            
    if len(pool) == 0: # no picks resulted in a valid samplew
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

# function to compute lower and upper thresholds
def _compute_threshold(sample_dem_ratio_sum, picks_remain, state_sz, limit):
    p = float(limit * state_sz - sample_dem_ratio_sum) / picks_remain

    # sanity check: p should be a solution to this equation
    assert _almost_equal((sample_dem_ratio_sum + p * picks_remain)/state_sz, limit)

    return p

# does value lie within margin of target?
def _within(value, target, margin):
    return abs(value - target) < margin

# compute average of the array
def _average(arr):
    return float(sum(arr))/len(arr)

# to compare floats ignoring rounding errors
def _almost_equal(a, b):
    return abs(a - b) <= .000001

class dummy:
    pass
