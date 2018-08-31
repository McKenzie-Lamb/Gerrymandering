import sys
sys.path.append('./src/')

import two_test_search
import json

##
# Function Parameters
##

state_dem_ratio = .52    # overall ratio of democratic votes
target_dem_seats = 10    # target number of democratic seats
state_total_seats = 18  # total number of seats in the state


# time(s) to run before giving up
max_time = 10             

# all the ratios will be below low cutoff or above high cutoff
safe_seat_low_cutoff = .49
safe_seat_high_cutoff = .51

# race between low and high is considered close (affects the tests we use)
close_race_low_cutoff = .45
close_race_high_cutoff = .55

# do output?
do_print = True

# ratios are needed for Levene test if the race is not close
# we read them from a file

with open('2014_data_levene_test.json', 'r') as f:
    levene_ratios = json.load(f)

print ('Gerrymandering state with vote ratio', state_dem_ratio , 'to', target_dem_seats, 'Democrat seats out of', state_total_seats)

# returns sorted list of ratios
ratios = two_test_search.TwoTestCustomGerrymanderTo(
    state_dem_ratio,
    state_total_seats,
    target_dem_seats,
    
    levene_ratios = levene_ratios,
    
    safe_seat_low_cutoff = safe_seat_low_cutoff,
    safe_seat_high_cutoff = safe_seat_high_cutoff,
    
    close_race_low_cutoff = close_race_low_cutoff,
    close_race_high_cutoff = close_race_high_cutoff,
    
    max_time = max_time,
    do_print = do_print
)

print ("Gerrymandered ratios:", ratios)

