function _find_bunch_to_move(mg, base_node_to_move, part_from)
    connected = false
    radius = bunch_radius
    bunch_to_move = [] #Declare for access to local scope variable in loop.
    while connected == false
        bunch_to_move = Set(LG.neighborhood(mg, base_node_to_move, radius))
        bunch_to_move = intersect(bunch_to_move, Set(MG.filter_vertices(mg, :part, part_from)))
        subgraph, vm = LG.induced_subgraph(mg, collect(bunch_to_move))
        if LG.is_connected(subgraph)
            connected = true
        else
            radius -= 1
        end
    end
    return bunch_to_move
end

function _do_move(mg, part_to, part_from, bunch_to_move)
    pop_to_move = sum([MG.get_prop(mg, n, :pop) for n in bunch_to_move])
    dems_to_move = sum([MG.get_prop(mg, n, :dems) for n in bunch_to_move])
    reps_to_move = sum([MG.get_prop(mg, n, :reps) for n in bunch_to_move])
    tot_to_move = dems_to_move + reps_to_move

    #Update dictionary of district data to reflect move.
    dist_data = MG.get_prop(mg, :dist_dict)
    dist_data[part_to].pop += pop_to_move
    dist_data[part_from].pop -= pop_to_move
    dist_data[part_to].dems += dems_to_move
    dist_data[part_from].dems -= dems_to_move
    dist_data[part_to].reps += reps_to_move
    dist_data[part_from].reps -= reps_to_move
    dist_data[part_to].tot += tot_to_move
    dist_data[part_from].tot -= tot_to_move
    UpdateDemProps(mg)
    MG.set_prop!(mg, :dist_dict, dist_data)

    #Update node prorties of moved nodes.
    for n in bunch_to_move
        MG.set_prop!(mg, n, :part, part_to)
    end
end


#= Makes a move: reassigns a connected set of nodes from one district to another.
If the proposed move would disconnect the district losing nodes, bail. =#
function MoveNodes(mg, part_to)
    part_to_nodes = MG.filter_vertices(mg, :part, part_to)
    boundary = Boundary(mg, part_to_nodes)
    boundary = collect(boundary)
    tries = 0
    connected = false
    while tries <= max_tries && connected == false
        #Find a connected boundary neighborhood to move.
        base_node_to_move = rand(boundary)
        part_from = MG.get_prop(mg, base_node_to_move, :part)
        bunch_to_move = _find_bunch_to_move(mg, base_node_to_move, part_from)

        #Try moving bunch_to_move from part_from to part_to.
        #First, check to see whether the move would disconnect part_from.
        if CheckConnectedWithoutBunch(mg, part_from, bunch_to_move)
            _do_move(mg, part_to, part_from, bunch_to_move)
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
function ShuffleNodes(mg)
    mg_temp = deepcopy(mg)
    # part_to = FindFarthestDist(mg)
    part_to = rand(1:MG.get_prop(mg, :num_parts))
    num_moves = rand(1:max_moves)
    # visited = IntSet()
    for i in 1:num_moves
        part_to, success = MoveNodes(mg, part_to)
        if success == false
            return mg_temp, false
        else
            # if in(part_to, visited)
            #     return mg, true
            # else
                # push!(visited, part_to)
            # end
        end
    end
    return mg, true
end


function _acceptance_prob(old_score, new_score, T)
    ap = exp((old_score - new_score)/T)
    if ap > 1
        return 1
    else
        return ap
    end
end

function SimulatedAnnealing(mg)
    global bunch_radius
    global Score
    Score = TargetParity #Choose score function.
    current_score = Score(mg)
    println("Initial Score: ", current_score)
    T = 1.0
    steps_remaining = Int(round(temperature_steps))
    swaps = [max_swaps, 0]
    while T > T_min
        i = 1
        while i <= swaps[1]
            new_mg = deepcopy(mg)
            new_mg, success = ShuffleNodes(new_mg)
            new_score = Score(new_mg)
            ap = _acceptance_prob(current_score, new_score, T)
            if ap > rand()
                if new_score < current_score
                    println("Score: ", new_score)
                end
                swaps[2] += 1
                mg = new_mg
                current_score = new_score
            else
                # println("T = ", T)
            end
            i += 1
        end
        steps_remaining -= 1
        bunch_radius = Int(floor(max_radius - (max_radius / temperature_steps) * (temperature_steps - steps_remaining)))
        println("-------------------------------------")
        println("Steps Remaining: ", steps_remaining)
        println("Bunch Radius: ", bunch_radius)
        T = T * alpha
        println("T = ", T)
        dem_percents = sort!(DemPercentages(mg))
        println("Dem percents: ", sort(dem_percents))
        println("Parity: ", DistanceToParity(mg))
        println("-------------------------------------")
        # if !AllConnected(mg)
        #     println("Connectedness broken.")
        #     break
        # end
    end
    return mg
end
