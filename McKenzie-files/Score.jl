#=This file contains various score functions for the RePartition module.=#


#=Measures taxicab distance to target, but throws away improvements beyond
targets: throw away district doesn't need to go below target;
districts to win don't need to go above safe percentage.
=#
function OneSided(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    percentages = sort([dist.dem_prop for dist in values(dist_data)])
    pops = sort([dist.pop for dist in values(dist_data)])
    parity = MG.get_prop(mg, :parity)
    throw_away_distance = maximum([0.0, percentages[1]-target[1]])
    safe_distance = norm([maximum([0.0, target[i] - percentages[i]]) for i in 2:num_parts])
    #sqrt(sum([(percentages[i]-target[i])^2 for i in 1:length(target)]))
    dist_to_parity = 100*(maximum(append!([0.1], [par_thresh * ((p-parity)/(parity * par_thresh))^2 for p in pops])))
    return throw_away_distance + safe_distance + dist_to_parity
end

#Euclidean distance to target democratic percentages
#in num_parts-dimensional space + parity score (squared).
function TargetParityCompactness(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    percentages = sort([dist.dem_prop for dist in values(dist_data)])
    pops = sort([dist.pop for dist in values(dist_data)])
    parity = MG.get_prop(mg, :parity)
    dist_to_parity = 100*(maximum(append!([0.1], [par_thresh * ((p-parity)/(parity * par_thresh))^2 for p in pops])))
    compactness = Compactness(mg)
    return norm(percentages-target) + dist_to_parity + compactness
end

#Euclidean distance to target democratic percentages
#in num_parts-dimensional space + parity score (squared).
function TargetParity(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    percentages = sort([dist.dem_prop for dist in values(dist_data)])
    pops = sort([dist.pop for dist in values(dist_data)])
    parity = MG.get_prop(mg, :parity)
    dist_to_parity = 100*(maximum(append!([0.1], [par_thresh * ((p-parity)/(parity * par_thresh))^2 for p in pops])))
    return norm(percentages-target) + dist_to_parity
end

#Euclidean distance to target democratic percentages
#in num_parts-dimensional space.
function DistToTarget(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    percentages = sort([dist.dem_prop for dist in values(dist_data)])
    pops = sort([dist.pop for dist in values(dist_data)])
    parity = MG.get_prop(mg, :parity)
    return norm(percentages-target)
end

#Euclidean distance from vector of percentages for districts to win to the line
#on which they are all equal.  Uses a vector projection.
function DistToEqual(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    percentages = sort([dist.dem_prop for dist in values(dist_data)])
    pops = sort([dist.pop for dist in values(dist_data)])
    ep = percentages[2:num_parts]
    el = [1 for i in 2:num_parts]
    dist_to_equal = norm(ep - (dot(ep, el)/dot(el, el))*el)
    return dist_to_equal
end

#=Calculates a parity score based on the maximum deviation above or below
parity.  Squaring imposes steep penalties once par_thresh is exceeded.
Also, maximum ensures score remains constant if maximum deviation is
below par_thresh.
=#
function Parity(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    pops = sort([dist.pop for dist in values(dist_data)])
    parity = MG.get_prop(mg, :parity)
    return 100*(maximum(append!([par_thresh], [par_thresh * ((p-parity)/(parity * par_thresh))^2 for p in pops])))
end

#=Three componenets: distance to target of throw-away district,
distance to equality line of districts we want to win,
distance to parity.
=#
function Component(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    percentages = sort([dist.dem_prop for dist in values(dist_data)])
    pops = sort([dist.pop for dist in values(dist_data)])
    parity = MG.get_prop(mg, :parity)
    dist_to_target = abs(percentages[1]-target[1])
    dist_to_parity = 100*(maximum(append!([par_thresh], [par_thresh * ((p-parity)/(parity * par_thresh))^2 for p in pops])))
    ep = percentages[2:num_parts]
    el = [1 for i in 2:num_parts]
    dist_from_equal = norm(ep - (dot(ep, el)/dot(el, el))*el)
    return dist_to_target + 4 * dist_from_equal + dist_to_parity
end
