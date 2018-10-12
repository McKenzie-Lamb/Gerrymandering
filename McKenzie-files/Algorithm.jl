function _find_bunch_to_move(dist_dict, base_node_to_move, part_from)
    connected = false
    radius = bunch_radius
    bunch_to_move = [] #Declare for access to local scope variable in loop.
    while connected == false
        bunch_to_move = Set(LG.neighborhood(mg, base_node_to_move, radius))
        bunch_to_move = intersect(bunch_to_move, dist_dict[part_from].vtds)
        subgraph, vm = LG.induced_subgraph(mg, collect(bunch_to_move))
        if LG.is_connected(subgraph)
            connected = true
        else
            radius -= 1 #Decrease radius until bunch_to_move is connected.
        end
    end
    return bunch_to_move
end

function _do_move(dist_dict, part_to, part_from, bunch_to_move)
    pop_to_move = sum([MG.get_prop(mg, n, :pop) for n in bunch_to_move])
    dems_to_move = sum([MG.get_prop(mg, n, :dems) for n in bunch_to_move])
    reps_to_move = sum([MG.get_prop(mg, n, :reps) for n in bunch_to_move])
    tot_to_move = dems_to_move + reps_to_move

    #Update dictionary of district data to reflect.
    dist_dict[part_to].pop += pop_to_move
    dist_dict[part_from].pop -= pop_to_move
    dist_dict[part_to].dems += dems_to_move
    dist_dict[part_from].dems -= dems_to_move
    dist_dict[part_to].reps += reps_to_move
    dist_dict[part_from].reps -= reps_to_move
    dist_dict[part_to].tot += tot_to_move
    dist_dict[part_from].tot -= tot_to_move

    setdiff!(dist_dict[part_from].vtds, bunch_to_move)
    union!(dist_dict[part_to].vtds, bunch_to_move)

    # dist_dict[part_from].pop = sum([MG.get_prop(mg, n, :pop) for n in dist_dict[part_from].vtds])
    # dist_dict[part_to].pop = sum([MG.get_prop(mg, n, :pop) for n in dist_dict[part_to].vtds])
    # dist_dict[part_from].dems = sum([MG.get_prop(mg, n, :dems) for n in dist_dict[part_from].vtds])
    # dist_dict[part_to].dems = sum([MG.get_prop(mg, n, :dems) for n in dist_dict[part_to].vtds])
    # dist_dict[part_from].reps = sum([MG.get_prop(mg, n, :reps) for n in dist_dict[part_from].vtds])
    # dist_dict[part_to].reps = sum([MG.get_prop(mg, n, :reps) for n in dist_dict[part_to].vtds])
    # dist_dict[part_from].tot = dist_dict[part_from].dems + dist_dict[part_from].reps

    UpdateDemProps(dist_dict)
    # println("Pops: ", sort([dist.pop for dist in values(dist_dict)]))
end


#= Makes a move: reassigns a connected set of nodes from one district to another.
If the proposed move would disconnect the district losing nodes, bail. =#
function MoveNodes(dist_dict, part_to)
    part_to_nodes = dist_dict[part_to].vtds
    boundary = Boundary(part_to_nodes)
    boundary = collect(boundary)
    tries = 0
    connected = false
    while tries <= max_tries && connected == false
        #Find a connected boundary neighborhood to move.
        base_node_to_move = rand(boundary)
        part_from = FindDistrictNum(dist_dict, base_node_to_move)
        bunch_to_move = _find_bunch_to_move(dist_dict, base_node_to_move, part_from)

        #Try moving bunch_to_move from part_from to part_to.
        #First, check to see whether the move would disconnect part_from.
        if CheckConnectedWithoutBunch(dist_dict, part_from, bunch_to_move)
            _do_move(dist_dict, part_to, part_from, bunch_to_move)
            connected = true
            return part_from, true
        else
            tries += 1
            continue
        end
    end
    return part_to, false
end

#= Makes a sequence of node moves (length of sequence set as global const.)
For each step after the first in the sequence, the district to receive
nodes is the one that lost nodes in the previous step. =#
function ShuffleNodes(dist_dict)
    dist_dict_temp = deepcopy(dist_dict)
    # part_to = FindFarthestDist(mg)
    part_to = rand(1:num_parts)
    num_moves = rand(1:max_moves)
    # visited = IntSet()
    for i in 1:num_moves
        part_to, success = MoveNodes(dist_dict, part_to)
        if success == false
            return dist_dict_temp, false
        end
    end
    return dist_dict, true
end


function _acceptance_prob(old_score, new_score, T)
    ap = exp((old_score - new_score)/T)
    if ap > 1
        return 1
    else
        return ap
    end
end

function SimulatedAnnealing(dist_dict)
    global bunch_radius
    global Score
    global par_thresh
    Score = TargetParity #Choose score function.
    current_score = Score(dist_dict)
    println("Initial Score: ", current_score)
    T = 1.0
    steps_remaining = Int(round(temperature_steps))
    swaps = [max_swaps, 0]
    while T > T_min
        i = 1
        while i <= swaps[1]
            new_dist_dict = deepcopy(dist_dict)
            new_dist_dict, success = ShuffleNodes(new_dist_dict)
            new_score = Score(new_dist_dict)
            ap = _acceptance_prob(current_score, new_score, T)
            if ap > rand()
                if new_score < current_score
                    println("Score: ", new_score)
                end
                swaps[2] += 1
                dist_dict = new_dist_dict
                current_score = new_score
            else
                #
            end
            # println("Score: ", current_score)
            i += 1
        end
        steps_remaining -= 1
        bunch_radius = Int(floor(max_radius - (max_radius / temperature_steps) * (temperature_steps - steps_remaining)))
        # par_thresh = 0.1 - ((0.1-0.01)/temperature_steps)*(temperature_steps - steps_remaining)
        println("-------------------------------------")
        println("Steps Remaining: ", steps_remaining)
        # println("Parity Threshold: ", par_thresh)
        println("Bunch Radius: ", bunch_radius)
        T = T * alpha
        println("T = ", T)
        dem_percents = sort!(DemPercentages(dist_dict))
        println("Dem percents: ", sort(dem_percents))
        println("Parity: ", DistanceToParity(dist_dict))
        println("-------------------------------------")
        # if !AllConnected(mg)
        #     println("Connectedness broken.")
        #     break
        # end
    end
    return dist_dict
end
