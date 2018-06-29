import itertools, copy, math

class Dummy:
    pass

def almost_equal(a, b):
    return abs(a - b) <= .00001

def within(val, conf):
    return abs(val - conf.target) <= conf.margin

def combos_old(district_ls, so_far, combo_avgs, conf):
    sz = conf.state_sz
    if len(so_far) == sz:
        add_combo(combo_avgs, so_far)
        return
    
    for d in district_ls:
        if d in so_far:
            continue
        so_far.append(d)
        combos_old(district_ls, so_far, combo_avgs, conf)
        so_far.pop()
    
def print_dict(combo_avgs, conf = None):
    ls = [a for a in combo_avgs]
    ls.sort()

    for a in ls:
        if conf == None or within(float(a)/100, conf):
            print(a, ": ", combo_avgs[a])
            
def compare_dict(combo_avgs, combo_avgs_full, conf):
    factor = math.factorial(conf.state_sz)
    
    for a in combo_avgs:
        if conf == None or within(float(a)/100, conf):
            if a not in combo_avgs_full:
                return False
            if not almost_equal(combo_avgs[a]*factor, combo_avgs_full[a]):
                return False
    return True
    

def add_combo(combo_avgs, combo, factor = 1):
    avg = sum(combo)/len(combo)
    avg = round(avg*100)

    if avg not in combo_avgs:
        combo_avgs[avg] = 0.0
        
    combo_avgs[avg] += float(factor)
        
def generate_uniform(state_size, country_size):
    districts = [float(i)/(country_size-1) for i in range(country_size)]
    combos_set = set(itertools.combinations(districts, state_size))

    combo_avgs = {}

    for combo in combos_set:
        add_combo(combo_avgs, combo)
        

    res = Dummy()

    res.districts = districts
    res.combo_avgs = combo_avgs

    return res


