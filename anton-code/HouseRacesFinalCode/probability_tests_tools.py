from __future__ import print_function

import sys
sys.path.append('../')

from include_lite import *

import itertools, copy

def smpl_process(inx, seat_dist, conf):
    smpl = [conf.districts[i] for i in inx]
    
    votes = sum([rt * pop for rt, pop in smpl])
    pop = sum([pop for rt, pop in smpl])
    
    if within(votes/pop, conf.target, conf.margin):
        st = sum([1 for rt, pop in smpl if rt > .5])
        seat_dist[st] += 1

def prep_dist_inx(conf, prepend):
    dist_inx = list(range(len(conf.districts)))

    for i in prepend:
        dist_inx.remove(i)
    return dist_inx

def generate_all(conf, prepend = []):
    state_sz = conf.state_sz - len(prepend)
    country_sz = conf.country_sz - len(prepend)

    dist_inx = prep_dist_inx(conf, prepend)
    
    combos_set = set(itertools.combinations(dist_inx, state_sz))
    assert len(combos_set) == nCr(country_sz, state_sz)

    seat_dist = [0]*(conf.state_sz+1)

    for c in combos_set:
        smpl_process(prepend + list(c), seat_dist, conf)

    return seat_dist

def generate_random(conf, prepend = []):
    repeats = conf.repeats
    seat_dist = [0.0]*(conf.state_sz+1)
    
    dist_inx = prep_dist_inx(conf, prepend)
    
    for i in range(repeats):
        c = random.sample(dist_inx, conf.state_sz - len(prepend))
        smpl_process(prepend + list(c), seat_dist, conf)
        #smpl_process(c, seat_dist, conf)
        
    return seat_dist

def per_conv(f):
    return str(round(f*100, 2))+"%"

def success_rate_raw(seat, rp):
    return sum(seat)/rp

def success_rate(seat, rp):
    return per_conv(success_rate_raw(seat, rp))

def success_rate_err(seat, rp, p):
    assert p != 0
    assert rp != 0
    
    sr = success_rate_raw(seat, rp)
    SD = math.sqrt(p*(1-p)/rp)
    er = (sr - p)/SD        
    if er > 0:
        pp = '+'
    else:
        pp = ''
    er = pp + str(round(er, 1))
    return per_conv(sr) + " (" + er + ")"

def threshold(vote_now, pop_now, picks_remain, pop_per_pick, threshold):
    remain_pop = picks_remain * pop_per_pick
    final_pop = pop_now + remain_pop
    final_vote = final_pop * threshold
    missing_vote = final_vote - vote_now

    p = missing_vote / remain_pop

    assert almost_equal((vote_now + p * picks_remain * pop_per_pick)/(pop_now + picks_remain * pop_per_pick), threshold)

    return p
