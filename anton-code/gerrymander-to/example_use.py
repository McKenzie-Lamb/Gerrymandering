import sys
sys.path.append('./src/')

import two_test_gerrymander_to

state_name = 'WI'     # used to determine total number of districts, as well as some other parameters
state_dem_ratio = .5  # overall ratio of democratic votes
target_dem_seats = 5  # target number of democratic seats

# optional parameter(s)
# quiet = True          # for no output
# max_tries = 100       # how many attempts to run before giving up
# max_time = 60         # time (s) to run before giving up

# returns sorted list of ratios
print ('Gerrymandering', state_name, 'to', target_dem_seats, 'Democarat seats')
print (two_test_gerrymander_to.TwoTestGerrymanderTo(state_name, state_dem_ratio, target_dem_seats, max_time = 10))



# rough range of seats for which the function above would find a valid distribution
print(state_name, 'valid range of seats', two_test_gerrymander_to.TwoTestGetRange(state_name), '(approximate)')
