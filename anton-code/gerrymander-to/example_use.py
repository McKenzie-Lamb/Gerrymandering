import sys
sys.path.append('./src/')

import two_test_gerrymander_to as ttgt

state_name = 'WI'     # used to determine total number of districts, as well as some other parameters
state_dem_ratio = .5  # overall ratio of democratic votes
target_dem_seats = 1  # target number of democratic seats
max_tries = 100       # how many attempts to run before giving up

# optional parameter(s)
# quiet = True for no output

# returns sorted list of ratios
print ('Gerrymandering', state_name, 'to', target_dem_seats, 'Democarat seats')
try:
    print (ttgt.TwoTestGerrymanderTo(state_name, state_dem_ratio, target_dem_seats, max_tries))
except:
    print('Failed.')



# rough range of seats for which the function above would find a valid distribution
print(state_name, 'valid range of seats', ttgt.TwoTestGetRange(state_name), '(approximate)')
