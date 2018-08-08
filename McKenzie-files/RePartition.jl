module RePartition
using Colors
using PyCall
using LightGraphs; LG = LightGraphs
using MetaGraphs; MG = MetaGraphs
unshift!(PyVector(pyimport("sys")["path"]), "")
@pyimport networkx; nx = networkx
cd("/Users/lambm/Documents/GitHub/Gerrymandering/McKenzie-files")
@pyimport RandomPartitionedGraph2; RPG = RandomPartitionedGraph2
using GraphPlot, Compose
GP = GraphPlot
include("PrintPartition.jl")
include("Districts.jl")

# using Districts

#Graph parameters
const size = 1000
const num_parts = 8
const dem_mean = 0.5
const dem_sd = 0.5
const rand_graph = false
const filename = "whole_map_contig_point_adj.gpickle"

#Simulated annealing parameters
const target = [8*51-55*7, 55, 55, 55, 55, 55, 55, 55]
# const target = append!([50 - 5 * (num_parts - 1)], [55 for n in 1:(num_parts - 1)])
print(target)
const num_moves = 2
const bunch_radius = 2
const T_min = 0.00001
const alpha = 0.95
const max_swaps = 200
const sa_steps = log(alpha, T_min)

function CalculateDemPercentage(mg, part)
    part_nodes = MG.filter_vertices(mg, :part, part)
    part_pop = sum([MG.get_prop(mg, v, :pop) for v in part_nodes])
    part_dems = sum([MG.get_prop(mg, v, :dems) for v in part_nodes])
    return 100 * (part_dems / part_pop)
end

function DemPercentages(mg)
    return [CalculateDemPercentage(mg, part) for part in 1:MG.get_prop(mg, :num_parts)]
end

function CalculateDistData(mg, part)
    d = District(0, 0, 0)
    part_nodes = MG.filter_vertices(mg, :part, part)
    d.pop = sum([MG.get_prop(mg, v, :pop) for v in part_nodes])
    d.dems = sum([MG.get_prop(mg, v, :dems) for v in part_nodes])
    d.dem_prop = 100 * (d.dems / d.pop)
    return d
end


function SafeDemSeats(mg)
    percentages = DemPercentages(mg)
    return length([p for p in percentages if p >= 54])
end

function Boundary(mg, nodes)
    b_list = Set()
    for v in nodes
        union!(b_list, LG.neighbors(mg, v))
    end
    setdiff!(b_list, nodes)
    return b_list
end

function CalculateParity(mg)
    total_pop = sum([MG.get_prop(mg, v, :pop) for v in MG.vertices(mg)])
    MG.set_prop!(mg, :parity, total_pop / MG.get_prop(mg, :num_parts))
end

function ParityCheckOne(mg, part)
    part_nodes = MG.filter_vertices(mg, :part, part)
    part_pop = sum([MG.get_prop(mg, v, :pop) for v in part_nodes])
    parity = MG.get_prop(mg, :parity)
    threshold = MG.get_prop(mg, :par_thresh)
    return abs(part_pop - parity)/parity < threshold
end

function ParityCheckAll(mg)
    parity_bool = true
    for part in 1:MG.get_prop(mg, :num_parts)
        if !ParityCheckOne(mg, part)
            parity_bool = false
            break
        end
    end
    return parity_bool
end

function PartConnected(mg, part)
    part_nodes = MG.filter_vertices(mg, :part, part)
    subgraph, vm = LG.induced_subgraph(mg, part_nodes)
    return LG.is_connected(subgraph)
end

function AllConnected(mg)
    connected = true
    for part in 1:MG.get_prop(mg, :num_parts)
        if !PartConnected(mg, part)
            connected = false
            break
        end
    end
    return connected
end


#Always >= 0.  Closer to 0 is better.
function Score(mg, target)
    dist_data = MG.get_prop(mg, :dist_dict)
    percentages = sort([dist.dem_prop for dist in values(dist_data)])
    return sqrt(sum([(percentages[i]-target[i])^2 for i in 1:length(target)]))
end

#Create a randomly generated graph and partition it using Metis (via Python)
function InitialGraphPartition()
    G, parts = RPG.MakeGraphPartition(size = size, num_parts = num_parts,
            dem_sd = dem_sd, filename = filename, rand_graph = rand_graph)
    parts = [i+1 for i in parts]
    g = LG.SimpleGraph()
    LG.add_vertices!(g, length(G[:nodes]()))
    for e in G[:edges]()
        LG.add_edge!(g, (e[1]+1, e[2]+1))
    end
    mg = MG.MetaGraph(g)

    MG.set_prop!(mg, :num_parts, num_parts)
    MG.set_prop!(mg, :par_thresh, 0.1)

    for d in nx.get_node_attributes(G,"pop")
        # println(d[1], " ** ", d[2])
        MG.set_prop!(mg, d[1]+1, :pop, d[2])
    end

    CalculateParity(mg)

    for d in nx.get_node_attributes(G,"dem")
        MG.set_prop!(mg, d[1]+1, :dems, d[2])
    end

    for i in 1:length(parts)
        MG.set_prop!(mg, i, :part, parts[i])
    end

    dist_dict = Dict(part => CalculateDistData(mg, part) for part in 1:num_parts)
    MG.set_prop!(mg, :dist_dict, dist_dict)
    # println("Dist Data = ", dist_dict)
    return mg, G
end


function CheckDictParity(mg, dist_data)
    parity_bool = true
    parity = MG.get_prop(mg, :parity)
    threshold = MG.get_prop(mg, :par_thresh)
    for part in 1:MG.get_prop(mg, :num_parts)
        if !(abs(dist_data[part].pop - parity)/parity < threshold)
            # println("Parity Break: ", part, ", ", dist_data[part].pop, ", ", parity)
            parity_bool = false
            break
        end
    end
    return parity_bool
end

function CheckConnectedWithoutBunch(mg, part_from, bunch_to_move)
    part_nodes = Set(MG.filter_vertices(mg, :part, part_from))
    setdiff!(part_nodes, bunch_to_move)
    subgraph, vm = LG.induced_subgraph(mg, collect(part_nodes))
    return LG.is_connected(subgraph)
end

#For debugging.
function MoveCheck(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    parity = MG.get_prop(mg, :parity)
    margin = parity * MG.get_prop(mg, :par_thresh)
    for d in keys(dist_data)
        println("Margin = ", margin)
        println("District: ", d, ", ", dist_data[d].pop - parity)
    end
    part_to = 1
    bunch_radius = 0
    part_to_nodes = MG.filter_vertices(mg, :part, part_to)
    boundary = Boundary(mg, part_to_nodes)
    base_node_to_move = rand(boundary)
    part_from = MG.get_prop(mg, base_node_to_move, :part)
    radius = rand(0:bunch_radius)
    bunch_to_move = Set(LG.neighborhood(mg, base_node_to_move, radius))
    bunch_to_move = intersect(bunch_to_move, Set(MG.filter_vertices(mg, :part, part_from)))
    pop_to_move = sum([MG.get_prop(mg, n, :pop) for n in bunch_to_move])
    dems_to_move = sum([MG.get_prop(mg, n, :dems) for n in bunch_to_move])
    println("PTM, DAM: ", (pop_to_move, dems_to_move))
    println("Parity Margin = ", MG.get_prop(mg, :par_thresh))
    dist_data = MG.get_prop(mg, :dist_dict)
    dist_data[part_to].pop += pop_to_move
    dist_data[part_from].pop -= pop_to_move
    CheckDictParity(mg, dist_data)
end

function MoveNodes(mg, part_to)
    part_to_nodes = MG.filter_vertices(mg, :part, part_to)
    boundary = Boundary(mg, part_to_nodes)
    base_node_to_move = rand(boundary)
    part_from = MG.get_prop(mg, base_node_to_move, :part)
    radius = rand(0:bunch_radius)
    bunch_to_move = Set(LG.neighborhood(mg, base_node_to_move, radius))
    bunch_to_move = intersect(bunch_to_move, Set(MG.filter_vertices(mg, :part, part_from)))
    # println(length(Set(MG.filter_vertices(mg, :part, part_from))))
    # println("Bunch size in part_from = ", length(bunch_to_move))
    if CheckConnectedWithoutBunch(mg, part_from, bunch_to_move)
        pop_to_move = sum([MG.get_prop(mg, n, :pop) for n in bunch_to_move])
        dems_to_move = sum([MG.get_prop(mg, n, :dems) for n in bunch_to_move])
        dist_data = MG.get_prop(mg, :dist_dict)
        dist_data[part_to].pop += pop_to_move
        dist_data[part_from].pop -= pop_to_move
        dist_data[part_to].dems += dems_to_move
        dist_data[part_from].dems -= dems_to_move
        dist_data[part_to].dem_prop = 100 * (dist_data[part_to].dems / dist_data[part_to].pop)
        dist_data[part_from].dem_prop = 100 * (dist_data[part_from].dems / dist_data[part_from].pop)
        MG.set_prop!(mg, :dist_dict, dist_data)
        for n in bunch_to_move
            MG.set_prop!(mg, n, :part, part_to)
        end
        return part_from, true
    else
        return part_from, false
    end
end

function ShuffleNodes(mg)
    mg_temp = deepcopy(mg)
    part_to = rand(1:MG.get_prop(mg, :num_parts))
    for i in 1:num_moves
        part_to, success = MoveNodes(mg, part_to)
        if success == false
            # println("Failed")
            return mg_temp, false
        end
    end
    # ac = AllConnected(mg)
    if !CheckDictParity(mg, MG.get_prop(mg, :dist_dict))
        return mg_temp, false
    else
        # println("Succeeded.")
        return mg, true
    end
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
    current_score = Score(mg, target)
    println("Initial Score: ", current_score)
    T = 1.0
    steps = 0
    swaps = [max_swaps, 0]
    while T > T_min
        i = 1
        while i <= swaps[1]
            new_mg = deepcopy(mg)
            new_mg, success = ShuffleNodes(new_mg)
            new_score = Score(new_mg, target)
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
        steps += 1
        println("Steps Remaining: ", sa_steps - steps)
        T = T * alpha
        println("T = ", T)
    end
    return mg
end


# @time PartitionDict(mg)
function RunFunc(;print_graph = false, sim = false)
    mg, G = InitialGraphPartition()

    #= Set x and y coordinates of nodes.  Takes a long time.
    Comment out if not plotting before and after.=#
    if print_graph == true
        #For randomly generated graph.
        if rand_graph == true
            pos = nx.spectral_layout(G)
            locs_x = [pos[node_coords][1] for node_coords in sort(collect(keys(pos)))]
            locs_y = [pos[node_coords][2] for node_coords in sort(collect(keys(pos)))]
        else
            #For gpickle files.
            pos_dict = Dict(nx.get_node_attributes(G,"pos"))
            locs_x = [pos_dict[n][1] for n in G[:nodes]()]
            locs_y = [-pos_dict[n][2] for n in G[:nodes]()]
        end
        # println(locs_x)
        PrintPartition(mg, locs_x, locs_y, name = "before.svg")
    end


    #Record before data.
    current_score = Score(mg, target)
    println("Initial Score: ", current_score)
    connected_before = AllConnected(mg)
    connected_after = ParityCheckAll(mg)
    dem_percent_before = DemPercentages(mg)
    mean_dem_percent_before = mean(dem_percent_before)
    safe_dem_seats_before = SafeDemSeats(mg)

    #Print before data.
    println("Number of vertices = ", LG.nv(mg))
    println("Connected? ", connected_before)
    println("Parity? ", connected_after)
    println("Dem percents = ", dem_percent_before)
    println("Mean dem percent = ", mean_dem_percent_before)
    println("Safe dem seats = ", safe_dem_seats_before)

    # for i in 1:10
    #     MoveCheck(mg)
    # end

    if sim == true
        @time mg = SimulatedAnnealing(mg)

        #Print before and after data.
        println("Number of vertices = ", LG.nv(mg))
        println("Connected before? ", connected_before)
        println("Parity before? ", connected_after)
        println("Dem percents before = ", dem_percent_before)
        println("Mean dem percent before = ", mean_dem_percent_before)
        println("Safe dem seats before = ", safe_dem_seats_before)

        println("Final Score = ", Score(mg, target))
        println("Connected after? ", AllConnected(mg))
        println("Parity after? ", ParityCheckAll(mg))
        dem_percents_after = DemPercentages(mg)
        println("Dem percents after = ", dem_percents_after)
        println("Mean dem percent after = ", mean(dem_percents_after))
        println("Safe dem seats after = ", SafeDemSeats(mg))
        if print_graph == true
            PrintPartition(mg, locs_x, locs_y, name = "after.svg")
        end
    end
    return mg, G
end

# mg, G = RePartition.RunFunc(print_graph = true, sim = true)
end

#Testing Code
using RePartition
mg, G = RePartition.RunFunc(print_graph = true, sim = true)
