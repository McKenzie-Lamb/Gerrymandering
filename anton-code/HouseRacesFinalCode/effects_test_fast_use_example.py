import math

import effects_test_fast
import effects_test_tools

##
# Example 1: toy distribution
## 

ambient_districts = [float(i)/100 for i in range(100)] # uniformly distributed districts
state_sz = 10          # sample 10 of the districts
ratio_target = .65     # with ratio of votes close to 65%
ratio_margin = .001    # within .1% error
max_samples = 10000    # number of samples to collect
max_attempts = 100000  # number of attempts to get samples (though almost every attempt should be successful)

print ("Generating samples for the toy example...")

seat_prob_dist, all_samples = effects_test_fast.generate_many_samples(
                                                    ambient_districts,
                                                    state_sz,
                                                    ratio_target,
                                                    ratio_margin,
                                                    max_attempts,
                                                    max_samples)

print ("Toy state seat distribution:", seat_prob_dist)
print ("Toy state range of valid seats:", effects_test_tools.valid_range(seat_prob_dist))
print ()


##
# Example 2: We load distribution of votes from 2014 using a file.
## 

state_name = 'IL'
districts_file_path = 'districts_2014_adjusted.json'

# load ratios of votes in every district in the state
state_ratios = effects_test_tools.load_state(districts_file_path, state_name)

# load all districts, excluding districts of the analyzed state
ambient_districts = effects_test_tools.load_ambient_districts(districts_file_path, exclude_state=state_name)

state_sz = len(state_ratios)
ratio_target = sum(state_ratios)/len(state_ratios)
ratio_margin = .001
max_samples = 10000
max_attempts = 100000

print ("Generating samples for 2014", state_name, "...")

seat_prob_dist, all_samples = effects_test_fast.generate_many_samples(
                                                    ambient_districts,
                                                    state_sz,
                                                    ratio_target,
                                                    ratio_margin,
                                                    max_attempts,
                                                    max_samples)

print (state_name, "seat distribution:", seat_prob_dist)
print (state_name, "range of valid seats:", effects_test_tools.valid_range(seat_prob_dist))
print ()
