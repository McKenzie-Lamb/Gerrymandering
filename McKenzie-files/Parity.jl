function CalculateParity()
    total_pop = sum([MG.get_prop(mg, v, :pop) for v in MG.vertices(mg)])
    MG.set_prop!(mg, :parity, total_pop / num_parts)
end

function ParityCheckOne(dist_dict, part)
    part_nodes = dist_dict[part].vtds
    part_pop = sum([MG.get_prop(mg, v, :pop) for v in part_nodes])
    parity = MG.get_prop(mg, :parity)
    return abs(part_pop - parity)/parity < par_thresh
end

function DistanceToParity(dist_dict)
    pops = sort([dist.pop for dist in values(dist_dict)])
    # println("####Pops##### : ", pops)
    parity = MG.get_prop(mg, :parity)
    return [100.0*((p-parity)/parity) for p in pops]
end


function ParityCheckAll(dist_dict)
    parity_bool = true
    for part in 1:num_parts
        if !ParityCheckOne(dist_dict, part)
            parity_bool = false
            break
        end
    end
    return parity_bool
end




#Check whether all districts are within par_thresh of population parity.
#Input: Dictionary of district structs.
#Output: true or false.
function CheckDictParity(dist_dict)
    parity_bool = true
    parity = MG.get_prop(mg, :parity)
    for part in 1:MG.get_prop(mg, :num_parts)
        if !(abs(dist_dict[part].pop - parity)/parity < par_thresh)
            # println("Parity Break: ", part, ", ", dist_dict[part].pop, ", ", parity)
            parity_bool = false
            break
        end
    end
    return parity_bool
end
