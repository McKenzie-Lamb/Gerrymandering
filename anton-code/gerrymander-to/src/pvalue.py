def pvalue_one_side(seat_dist, seat_num):
    pv_low = sum(seat_dist[:seat_num+1])/sum(seat_dist)
    pv_high = sum(seat_dist[seat_num:])/sum(seat_dist)

    return min([pv_low, pv_high])
