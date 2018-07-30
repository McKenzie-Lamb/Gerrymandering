import effects_test_fast

##
# Example 1: toy distribution
## 

ambient_districts = [float(i)/100 for i in range(100)]
state_sz = 10
ratio_target = .65
ratio_margin = .001
max_attempts = 100000
max_samples = 10000

seat_prob_dist, all_samples = effects_test_fast.generate_many_samples(
                                                    ambient_districts,
                                                    state_sz,
                                                    ratio_target,
                                                    ratio_margin,
                                                    max_attempts,
                                                    max_samples)

print (seat_prob_dist)
