module RePartition
using Colors
using PyCall
using LightGraphs; LG = LightGraphs
using MetaGraphs; MG = MetaGraphs
unshift!(PyVector(pyimport("sys")["path"]), "")
@pyimport networkx; nx = networkx
cd(dirname(Base.source_path()))
@pyimport RandomPartitionedGraph2; RPG = RandomPartitionedGraph2

#For compactness measure calculation.
# @pyimport matplotlib.pyplot as pyplot
# using PyPlot
@pyimport shapely
geom = shapely.geometry
poly = geom[:polygon]
Polygon = poly[:Polygon]
LinearRing = geom[:LinearRing]

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
# const filename = "contig_16_share.gpickle" #Texas (incomplete data)
const filename = "whole_map_contig_point_adj.gpickle" #Wisconsin
percent_dem = 50
const par_thresh = 0.1

#Simulated annealing parameters
const safe_percentage = 54
target = append!([num_parts*percent_dem-safe_percentage*(num_parts - 1)],
                 [safe_percentage for i in 1:(num_parts - 1)])
const num_moves = 2
const max_radius = 6
bunch_radius = max_radius
const alpha = 0.95
const temperature_steps = 150
const T_min = alpha^temperature_steps
const max_swaps = 150
# const sa_steps = log(alpha, T_min)

function CalculateDemPercentage(mg, part)
    part_nodes = MG.filter_vertices(mg, :part, part)
    part_tot = sum([MG.get_prop(mg, v, :tot) for v in part_nodes])
    part_dems = sum([MG.get_prop(mg, v, :dems) for v in part_nodes])
    return 100 * (part_dems / part_tot)
end

function DemPercentages(mg)
    return [CalculateDemPercentage(mg, part) for part in 1:MG.get_prop(mg, :num_parts)]
end

function CalculateDistData(mg, part)
    d = District(0, 0, 0, 0, 0)
    part_nodes = MG.filter_vertices(mg, :part, part)
    d.tot = sum([MG.get_prop(mg, v, :tot) for v in part_nodes])
    d.dems = sum([MG.get_prop(mg, v, :dems) for v in part_nodes])
    d.reps = sum([MG.get_prop(mg, v, :reps) for v in part_nodes])
    d.pop = sum([MG.get_prop(mg, v, :pop) for v in part_nodes])
    d.dem_prop = 100 * (d.dems / d.tot)
    return d
end


function SafeDemSeats(mg)
    percentages = DemPercentages(mg)
    return length([p for p in percentages if p >= 53])
end

function InteriorBoundary(mg, nodes)
    exterior_bdy = Boundary(mg, nodes)
    b_list = IntSet()
    for v in exterior_bdy
        union!(b_list, LG.neighbors(mg, v))
    end
    b_list = intersect(b_list, nodes)
    return b_list
end

#Not complete.  Will calculate convex hull compactness.
function Compactness(mg, part)
    bdy_nodes = InteriorBoundary(MG.filter_vertices(mg, :part, part))
end

#Returns the exterior node boundary of the set "nodes" within the graph "mg".
#Translated from NetworkX
function Boundary(mg, nodes)
    b_list = IntSet()
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
    return abs(part_pop - parity)/parity < par_thresh
end

function DistanceToParity(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    pops = sort([dist.pop for dist in values(dist_data)])
    # println("####Pops##### : ", pops)
    parity = MG.get_prop(mg, :parity)
    return [100.0*((p-parity)/parity) for p in pops]
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

#Returns true if all districts are connected, false otherwise.
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

function PartCompactness(mg, part)
    bdy_nodes = InteriorBoundary(mg, MG.filter_vertices(mg, :part, part))
    points = [MG.get_prop(mg, n, :pos) for n in bdy_nodes]
    poly = Polygon(points)
    area = poly[:area]
    # println("Area = ", area)
    convex_hull = poly[:convex_hull]
    ch_area = convex_hull[:area]
    # println("Convex Hull Area = ", ch_area)
    return area / ch_area
    # ring = LinearRing(points)
end

#=Measures taxicab distance to target, but throws away improvements beyond
targets: throw away district doesn't need to go below target;
districts to win don't need to go above safe percentage.
=#
function OneSidedScore(mg)
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
#in num_parts-dimensional space + parity score.
function TargetPlusParityScore(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    percentages = sort([dist.dem_prop for dist in values(dist_data)])
    pops = sort([dist.pop for dist in values(dist_data)])
    parity = MG.get_prop(mg, :parity)
    dist_to_parity = 100*(maximum(append!([0.1], [par_thresh * ((p-parity)/(parity * par_thresh))^2 for p in pops])))
    return norm(percentages-target) + dist_to_parity
end

#Euclidean distance to target democratic percentages
#in num_parts-dimensional space.
function DistToTargetScore(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    percentages = sort([dist.dem_prop for dist in values(dist_data)])
    pops = sort([dist.pop for dist in values(dist_data)])
    parity = MG.get_prop(mg, :parity)
    return norm(percentages-target)
end

#Euclidean distance from vector of percentages for districts to win to the line
#on which they are all equal.  Uses a vector projection.
function DistToEqualScore(mg)
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
function ParityScore(mg)
    dist_data = MG.get_prop(mg, :dist_dict)
    pops = sort([dist.pop for dist in values(dist_data)])
    parity = MG.get_prop(mg, :parity)
    return 100*(maximum(append!([par_thresh], [par_thresh * ((p-parity)/(parity * par_thresh))^2 for p in pops])))
end

#=Three componenets: distance to target of throw-away district,
distance to equality line of districts we want to win,
distance to parity.
=#
function ComponentScore(mg)
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

#Create a randomly generated graph and partition it using Metis (via Python)
function InitialGraphPartition()
    #Global variables to be updated based on graph data.
    global target
    global percent_dem

    #Import partitioned graph from Python/Metis.
    G, parts = RPG.MakeGraphPartition(size = size, num_parts = num_parts,
            dem_sd = dem_sd, filename = filename, rand_graph = rand_graph)

    #Increment by 1 because Julia starts counting at 1, Python starts at 0.
    parts = [i+1 for i in parts]

    #Create LG version of G.
    g = LG.SimpleGraph()
    LG.add_vertices!(g, length(G[:nodes]()))
    for e in G[:edges]()
        LG.add_edge!(g, (e[1]+1, e[2]+1)) #Increment because of counting difference.
    end
    mg = MG.MetaGraph(g)

    MG.set_prop!(mg, :num_parts, num_parts)

    #Copy population data from nx graph into MG graph
    for d in nx.get_node_attributes(G,"pop")
        # println(d[1], " ** ", d[2])
        MG.set_prop!(mg, d[1]+1, :pop, d[2])
    end

    CalculateParity(mg)

    #Copy democratic vote data from nx graph into MG graph
    for d in nx.get_node_attributes(G,"dem")
        if isnan(d[2])
            MG.set_prop!(mg, d[1]+1, :dems, 0)
        else
            MG.set_prop!(mg, d[1]+1, :dems, d[2])
        end
    end

    #Copy democratic vote data from nx graph into MG graph
    # rep_data =
    # println("Rep? ", rep_data)
    # if length(rep_data) == 0
    for d in nx.get_node_attributes(G,"rep")
        if isnan(d[2])
            MG.set_prop!(mg, d[1]+1, :reps, 0)
        else
            MG.set_prop!(mg, d[1]+1, :reps, d[2])
        end
    end

    #Construct total vote data: dem + rep
    for v in LG.vertices(mg)
        total = MG.get_prop(mg, v, :reps) + MG.get_prop(mg, v, :reps)
        MG.set_prop!(mg, v, :tot, total)
    end

    #Copy position (node coordinates) into MG graph.
    pos_dict = Dict(nx.get_node_attributes(G,"pos"))
    for node_num in keys(pos_dict)
        MG.set_prop!(mg, node_num+1, :pos, pos_dict[node_num])
    end

    #Insert district numbers into MG graph.
    for i in 1:length(parts)
        MG.set_prop!(mg, i, :part, parts[i])
    end

    #Create dictionary with district data (district objects).
    dist_dict = Dict(part => CalculateDistData(mg, part) for part in 1:num_parts)
    MG.set_prop!(mg, :dist_dict, dist_dict)
    # println("Dist Data = ", dist_dict)

    percent_dem = 100 * (sum([MG.get_prop(mg, d, :dems) for d in LG.vertices(mg)])
                / sum([MG.get_prop(mg, d, :tot) for d in LG.vertices(mg)]))
    println("Overal Dem Percentage = ", percent_dem)
    # target = [6, 6, 6, 6, 53, 53, 53, 53]
    target = append!([num_parts*percent_dem-safe_percentage*(num_parts - 1)],
                    [safe_percentage for i in 1:(num_parts - 1)])
    #sort([53.8291, 53.82, 53.7211, 31.523, 53.7479, 53.8298, 53.7259, 53.51])

    return mg, G
end

#Check whether all districts are within par_thresh of population parity.
#Input: Dictionary of district structs.
#Output: true or false.
function CheckDictParity(mg, dist_data)
    parity_bool = true
    parity = MG.get_prop(mg, :parity)
    for part in 1:MG.get_prop(mg, :num_parts)
        if !(abs(dist_data[part].pop - parity)/parity < par_thresh)
            # println("Parity Break: ", part, ", ", dist_data[part].pop, ", ", parity)
            parity_bool = false
            break
        end
    end
    return parity_bool
end

#Checks whether district part_from would be connected if the nodes in
#bunch_to_move were removed.  Returns true or false.
function CheckConnectedWithoutBunch(mg, part_from, bunch_to_move)
    part_nodes = Set(MG.filter_vertices(mg, :part, part_from))
    setdiff!(part_nodes, bunch_to_move)
    subgraph, vm = LG.induced_subgraph(mg, collect(part_nodes))
    return LG.is_connected(subgraph)
end

#Calculate proportions of democratic votes in each district.
#Record in dictionary of district objects.
function UpdateDemProps(mg)
    for (part, dist) in MG.get_prop(mg, :dist_dict)
        dist.dem_prop = 100*(dist.dems / dist.tot)
    end
end

#= Makes a move: reassigns a connected set of nodes from one district to another.
If the proposed move would disconnect the district losing nodes, bail. =#

function MoveNodes(mg, part_to)
    part_to_nodes = MG.filter_vertices(mg, :part, part_to)
    boundary = Boundary(mg, part_to_nodes)

    #Find a connected boundary neighborhood to move.
    connected = false
    radius = bunch_radius
    base_node_to_move = rand(collect(boundary))
    part_from = MG.get_prop(mg, base_node_to_move, :part)
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

    #Try moving bunch_to_move from part_from to part_to.
    #First, check to see whether the move would disconnect part_from.
    if CheckConnectedWithoutBunch(mg, part_from, bunch_to_move)
        pop_to_move = sum([MG.get_prop(mg, n, :pop) for n in bunch_to_move])
        dems_to_move = sum([MG.get_prop(mg, n, :dems) for n in bunch_to_move])
        reps_to_move = sum([MG.get_prop(mg, n, :reps) for n in bunch_to_move])
        tot_to_move = dems_to_move + reps_to_move
        dist_data = MG.get_prop(mg, :dist_dict)

        #Update dictionary of district data to reflect move.
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
        return part_from, true
    else
        return part_to, false
    end
end

#= Makes a sequence of node moves (length of sequence set as global const.)
For each step after the first in the sequence, the district to receive
nodes is the one that lost nodes in the previous step. =#
function ShuffleNodes(mg)
    mg_temp = deepcopy(mg)
    # part_to = FindFarthestDist(mg)
    part_to = rand(1:MG.get_prop(mg, :num_parts))
    for i in 1:num_moves
        part_to, success = MoveNodes(mg, part_to)
        if success == false
            # println("Failed")
            return mg_temp, false
        end
    end
    # ac = AllConnected(mg)
    # if !CheckDictParity(mg, MG.get_prop(mg, :dist_dict))
    #     return mg_temp, false
    # else
        # println("Succeeded.")
        return mg, true
    # end
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
    current_score = TargetPlusParityScore(mg)
    println("Initial Score: ", current_score)
    T = 1.0
    steps_remaining = Int(round(temperature_steps))
    swaps = [max_swaps, 0]
    while T > T_min
        i = 1
        while i <= swaps[1]
            new_mg = deepcopy(mg)
            new_mg, success = ShuffleNodes(new_mg)
            new_score = TargetPlusParityScore(new_mg)
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


# @time PartitionDict(mg)
function RunFunc(;print_graph = false, sim = false)
    mg, G = InitialGraphPartition()
    colors = []
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
        colors = PrintPartition(mg, locs_x, locs_y, name = "before.svg")
    end

    println("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    dem_percents = sort!(DemPercentages(mg))
    println("Dem percents: ", sort!(dem_percents))
    println("Parity: ", DistanceToParity(mg))
    println("District Data: ", MG.get_prop(mg, :dist_dict))
    println("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")


    #Record before data.
    # current_score = ComponentScore(mg)
    # println("Initial Score: ", current_score)
    connected_before = AllConnected(mg)
    parity_before = ParityCheckAll(mg)
    dem_percent_before = sort!(DemPercentages(mg))
    mean_dem_percent_before = mean(dem_percent_before)
    safe_dem_seats_before = SafeDemSeats(mg)

    #Print before data.
    println("Number of vertices = ", LG.nv(mg))
    println("Connected? ", connected_before)
    println("Parity? ", parity_before)
    println("Dem percents = ", dem_percent_before)
    println("Mean dem percent = ", mean_dem_percent_before)
    println("Safe dem seats = ", safe_dem_seats_before)
    println("Target = ", target)
    println("Initial Bunch Radius: ", bunch_radius)

    # for i in 1:10
    #     MoveCheck(mg)
    # end

    if sim == true
        @time mg = SimulatedAnnealing(mg)

        #Print before and after data.
        println("**************Before***************")
        println("Number of vertices = ", LG.nv(mg))
        println("Connected before? ", connected_before)
        println("Parity before? ", parity_before)
        println("Dem percents before = ", dem_percent_before)
        println("Mean dem percent before = ", mean_dem_percent_before)
        println("Safe dem seats before = ", safe_dem_seats_before)


        println("**************After***************")
        # println("Final Score = ", ComponentScore(mg))
        println("Connected after? ", AllConnected(mg))
        println("Parity after? ", ParityCheckAll(mg))
        println("Parity after: ", DistanceToParity(mg))
        dem_percents_after = sort!(DemPercentages(mg))
        println("Target = ", target)
        println("Dem percents after = ", sort!(dem_percents_after))
        println("Mean dem percent after = ", mean(dem_percents_after))
        println("Safe dem seats after = ", SafeDemSeats(mg))
        if print_graph == true
            colors = PrintPartition(mg, locs_x, locs_y, name = "after.svg")
        end
    end
    println("Colors: ", enumerate(colors))
    return mg, G, colors
end

# mg, G = RePartition.RunFunc(print_graph = true, sim = true)

#Testing function for compactness measure.
function CompactnessTest(mg, part)
    bdy_nodes = collect(InteriorBoundary(mg, MG.filter_vertices(mg, :part, part)))
    points = [MG.get_prop(mg, n, :pos) for n in bdy_nodes]
    bdy_sub_graph, a = LG.induced_subgraph(mg, bdy_nodes)
    ordered_points = LG.maximum_adjacency_visit(bdy_sub_graph)
    pts = [(Real(MG.get_prop(mg, p, :pos)[1]), Real(MG.get_prop(mg, p, :pos)[2])) for p in ordered_points]
    # println(pts)
    poly = Polygon(pts)
    area = poly[:area]
    println("Area = ", area)
    convex_hull = poly[:convex_hull]
    ch_area = convex_hull[:area]
    println("Convex Hull Area = ", ch_area)
    compactness = area / ch_area
    # ring = LinearRing([(0, 0), (0, 2), (1, 1),
    # (2, 2), (2, 0), (1, 0.8), (0, 0)])
    # x, y = ring.xy

    # fig = PyPlot.plot(x, y, color="#6699cc", alpha=0.7,
    #     linewidth=3, solid_capstyle="round", zorder=2)
    # fig.savefig("test.svg")
    # ring = LinearRing(points)
    return compactness
end

end

#Testing Code
using RePartition
mg, G, colors = RePartition.RunFunc(print_graph = true, sim = true)
