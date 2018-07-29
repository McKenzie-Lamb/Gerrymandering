import sys
sys.path.append('./src/')

import two_test_gerrymander_to as ttgt

###
# EXAMPLE 1
###

state_name = 'IL'     # used to determine total number of districts, as well as some other parameters
state_dem_ratio = .53  # overall ratio of democratic votes
target_dem_seats = 6  # target number of democratic seats

# optional parameter(s)
# quiet = True          # for no output
# max_tries = 100       # how many attempts to run before giving up
# max_time = 60         # time (s) to run before giving up

# returns sorted list of ratios
print ('Gerrymandering', state_name, 'to', target_dem_seats, 'Democrat seats')

print (ttgt.TwoTestStateGerrymanderTo(state_name, state_dem_ratio, target_dem_seats, max_time = 10))

# rough range of seats for which the function above would find a valid distribution
print(state_name, 'valid range of seats', ttgt.TwoTestGetRange(state_name), '(approximate)')

###
# EXAMPLE 2
###

# This function doesn't need the name of the state, but it needs to know number of total seats in the state
# It may run longer than the function above, but is much more flexible with its input

state_total_seats = 18

# optional parameter(s)
# max_time = 60         # time (s) to run before giving up

print ('Gerrymandering', state_name, 'to', target_dem_seats, 'Democrat seats (alternative algorithm)')

print (ttgt.TwoTestCustomGerrymanderTo(state_dem_ratio, state_total_seats, target_dem_seats, max_time = 10))
