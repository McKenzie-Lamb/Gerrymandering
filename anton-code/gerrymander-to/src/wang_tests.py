import scipy.stats, statistics, math

def margin_ttest_full(dist_arr):
    dem_props = [(d - .5) for d in dist_arr if d > .5]
    rep_props = [(.5 - d) for d in dist_arr if d <= .5]

    if len(dem_props) <= 0 or len(rep_props) <= 0:
        return 'na', 0
    
    tstat, pval_two =  scipy.stats.ttest_ind(dem_props, rep_props, equal_var = True)
    return ('pass' if pval_two > .05 else 'fail'), tstat

def margin_ttest(dist_arr):
    return margin_ttest_full(dist_arr)[0]

def mean_median_test_full(dist_arr):
    mean = statistics.mean(dist_arr)
    median = statistics.median(dist_arr)

    # assert abs(scipy.stats.sem(dist_arr) - statistics.stdev(dist_arr)/math.sqrt(len(dist_arr))) < .000001
    
    stat = (mean - median)/(.756 * scipy.stats.sem(dist_arr))

    if abs(stat) < 1.75:
        return 'pass', stat
    else:
        return 'fail', stat

def mean_median_test(dist_arr):
    return mean_median_test_full(dist_arr)[0]
    
def dem_wins(arr):
    return [a for a in arr if a > .5]
def rep_wins(arr):
    return [a for a in arr if a <= .5]

def levene_test_full(dist_arr, all_districts):
    local_dem = dem_wins(dist_arr)
    global_dem = dem_wins(all_districts)
    
    local_rep = rep_wins(dist_arr)
    global_rep = rep_wins(all_districts)

    if len(local_dem) == len(local_rep):
        return 'na', 0
    elif len(local_dem) > len(local_rep):
        local_final = local_dem
        global_final = global_dem
    else:
        local_final = local_rep
        global_final = global_rep

    stat, pval_two =  scipy.stats.levene(local_final, global_final)
    return ('pass' if pval_two > .05 else 'fail'), stat

def levene_test(dist_arr, all_districts):
    levene_test_full(dist_arr, all_districts)[0]

def pass_all_tests(dist_arr, all_districts, is_close_race):
    if margin_ttest(dist_arr) == 'fail':
        return False

    if is_close_race:
        if mean_median_test(dist_arr) == 'fail':
            return False
    else:
        if levene_test(dist_arr, all_districts) == 'fail':
            return False

    return True
         
def pass_all_tests_full(dist_arr, all_districts, is_close_race):
    res0, stat0 = margin_ttest_full(dist_arr)

    if res0 == 'fail':
        res0 = False
    else:
        res0 = True

    if is_close_race:
        res, stat =  mean_median_test_full(dist_arr)
    else:
        res, stat = levene_test_full(dist_arr, all_districts)

    if res == 'fail':
        res = False
    else:
        res = True
            
    return ((res0, stat0), (res, stat))

def __pvalue_one_side(seat_dist, seat_num):
    pv_low = sum(seat_dist[:seat_num+1])/sum(seat_dist)
    pv_high = sum(seat_dist[seat_num:])/sum(seat_dist)

    return min([pv_low, pv_high])

def pvalues_one_side(seat_dist):
    return [__pvalue_one_side(seat_dist, i) for i in range(len(seat_dist))]

def get_dem_seats(dist_arr):
    return sum([1 for d in dist_arr if d > .5])

if __name__ == '__main__':
    arr_d = [68.8, 75, 75]
    arr_r = [68.3, 69.5, 60.5, 61.7, 62.7]

    arr_d = [(d/100 - .5) for d in arr_d]
    arr_r = [(d/100 - .5) for d in arr_r]

    arr_all = [(.5 + d) for d in arr_d] + [(.5 - d) for d in arr_r]

    print (scipy.stats.ttest_ind(arr_d, arr_r, equal_var = True))
    print (margin_ttest(arr_all))
    print (mean_median_test(arr_all))

    mean = statistics.mean(arr_all)
    median = statistics.median(arr_all)

    print(mean, median, mean - median)


