import json

# compute p-value of a seat
def pvalue_one_side(seat_distribution, seat):
    pv_low = sum(seat_distribution[:seat+1])/sum(seat_distribution)
    pv_high = sum(seat_distribution[seat:])/sum(seat_distribution)

    return min([pv_low, pv_high])

# range of seats that have large p-value
def valid_range(seat_distribution, cut_off_p_value = .05):
    valid = [i for i in range(len(seat_distribution)) if pvalue_one_side(seat_distribution, i) > cut_off_p_value]
    assert len(valid) > 0

    return [min(valid), max(valid)]

# load ratios for districts of a state from a json file
def load_state(file_path, state_name):
    
    with open(file_path, 'r') as f:
        state_dict = json.load(f)

    return state_dict[state_name]

# load all districts from a json file, possibly excluding a state
def load_ambient_districts(file_path, exclude_state = None):
    
    with open(file_path, 'r') as f:
        state_dict = json.load(f)

    ambient_districts = []
        
    for st in state_dict:
        if st != exclude_state:
            ambient_districts += state_dict[st]

    return ambient_districts
