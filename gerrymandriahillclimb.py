# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 16:30:00 2017

@author: wr
"""

def one_step(state):
    new_plan = False
    while new_plan == False:
        new_plan = state.clone()
        d1 = new_plan.random_district()
        d2 = new_plan.random_district({d1})
        new_plan = new_plan.pairwise_swap(d1,d2)
        print(".",end="")
    return new_plan

def n_steps(state, n=1):
    new_plan = state
    for i in range(n):
        new_plan = one_step(new_plan)
        print("!",end="")
    return new_plan
    
def hill_climb(state,metric,stop_count,steps = 1):
    failures = 0
    count = 0
    while failures < stop_count and count < 1000:
        new_plan = n_steps(state,steps)
        if metric(new_plan,state):
            state = new_plan
            failures = 0
        else:
            failures += 1
        count += 1
        print("("+str(failures)+")",end="")
    return state
    