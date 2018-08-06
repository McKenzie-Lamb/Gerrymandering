module RePartition
using Colors
using PyCall
using LightGraphs; LG = LightGraphs
using MetaGraphs; MG = MetaGraphs
unshift!(PyVector(pyimport("sys")["path"]), "")
@pyimport networkx; nx = networkx
@pyimport RandomPartitionedGraph2; RPG = RandomPartitionedGraph2
using GraphPlot, Compose
GP = GraphPlot
include("PrintPartition.jl")
include("Districts.jl")
# using Districts

#Graph parameters
size = 400
num_parts = 8
dem_mean = 0.5
dem_sd = 0.5
filename = "small_map_no_discontiguos.gpickle"

#Simulated annealing parameters
target = [15, 55, 55, 55, 55, 55, 55, 55]
num_moves = 2
bunch_radius = 2


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
    parity_bool = true
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
    percentages = sort(DemPercentages(mg))
    return sum([abs(percentages[i]-target[i]) for i in 1:length(target)])
end

#Create a randomly generated graph and partition it using Metis (via Python)
function InitialGraphPartition()
    G, parts = RPG.MakeGraphPartition(size = size, num_parts = num_parts, dem_sd = dem_sd, filename = filename)
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

    return mg, G
end

function UpdatePart(mg, part_to, bunch_to_move)
    dist_dict = MG.get_prop(mg, :dist_dict)
    MG.set_prop!(mg, :dist_dict, dist_dict)
end

function CheckConnectedWithoutBunch(mg, part_from, bunch_to_move)
    part_nodes = Set(MG.filter_vertices(mg, :part, part_from))
    setdiff!(part_nodes, bunch_to_move)
    subgraph, vm = LG.induced_subgraph(mg, collect(part_nodes))
    return LG.is_connected(subgraph)
end

function MoveNodes(mg, part_to; nbhd_size = 2, bunch_radius = 0)
    part_to_nodes = MG.filter_vertices(mg, :part, part_to)
    boundary = Boundary(mg, part_to_nodes)
    base_node_to_move = rand(boundary)
    part_from = MG.get_prop(mg, base_node_to_move, :part)
    radius = rand(0:bunch_radius)
    bunch_to_move = Set(LG.neighborhood(mg, base_node_to_move, radius))
    # println("Bunch size = ", length(bunch_to_move))
    bunch_to_move = intersect(bunch_to_move, Set(MG.filter_vertices(mg, :part, part_from)))
    # println(length(Set(MG.filter_vertices(mg, :part, part_from))))
    # println("Bunch size in part_from = ", length(bunch_to_move))
    if CheckConnectedWithoutBunch(mg, part_from, bunch_to_move)
        for n in bunch_to_move
            MG.set_prop!(mg, n, :part, part_to)
        end
    # else
    #     println("Not connected.")
    end
    # UpdatePart(mg, part_to, bunch_to_move)
    return part_from
end

function ShuffleNodes(mg)
    mg_temp = deepcopy(mg)
    part_to = rand(1:MG.get_prop(mg, :num_parts))
    for i in 1:num_moves
        part_to = MoveNodes(mg, part_to, bunch_radius = bunch_radius)
    end
    # ac = AllConnected(mg)
    pca = ParityCheckAll(mg)
    if pca #!(ac & pca)
        return mg_temp, false
    else
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
    T_min = 0.0001
    alpha = 0.80
    swaps = [100, 0]
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
        T = T * alpha
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
        pos = nx.spectral_layout(G)
        locs_x = [pos[node_coords][1] for node_coords in sort(collect(keys(pos)))]
        locs_y = [pos[node_coords][2] for node_coords in sort(collect(keys(pos)))]

        #For gpickle files.
        # pos_dict = Dict(nx.get_node_attributes(G,"pos"))
        # locs_x = [pos_dict[n][1] for n in G[:nodes]()]
        # locs_y = [-pos_dict[n][2] for n in G[:nodes]()]
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
mg, G = RePartition.RunFunc(print_graph = false, sim = true)
