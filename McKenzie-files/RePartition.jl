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
# @pyimport shapely
# geom = shapely.geometry
# poly = geom[:polygon]
# Polygon = poly[:Polygon]
# LinearRing = geom[:LinearRing]

using GraphPlot, Compose
GP = GraphPlot
using Plots
# using PyPlot
using ConcaveHull; CH = ConcaveHull
include("PrintPartition.jl")
include("Districts.jl")
include("Score.jl")
include("InitialPartition.jl")
include("Algorithm.jl")

# using Districts

#Graph parameters
const size = 1000
const num_parts = 8
const dem_mean = 0.5
const dem_sd = 0.5
const rand_graph = false
# const filename = "contig_16_share.gpickle" #Texas (incomplete data)
const filename = "whole_map_contig_point_adj.gpickle" #Wisconsin
percent_dem = 50 #Placeholder.  Gets recalculated.
const par_thresh = 0.1

#Simulated annealing parameters
const safe_percentage = 54
target = append!([num_parts*percent_dem-safe_percentage*(num_parts - 1)],
                 [safe_percentage for i in 1:(num_parts - 1)])
dem_target = sort([0.055, 0.135, 0.135, 0.135, 0.135, 0.135, 0.135, 0.135])

const max_moves = 8
const max_radius = 2
const max_tries = 20
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
    part_nodes = MG.filter_vertices(mg, :part, part)
    points = [[MG.get_prop(mg, n, :pos)[1], MG.get_prop(mg, n, :pos)[2]] for n in part_nodes]
    ccave_hull = CH.concave_hull(points, 0)
    cvex_hull = CH.concave_hull(points, 10000)
    compactness = CH.area(ccave_hull) / CH.area(cvex_hull)
    return compactness
end

function Compactness(mg)
    return 100*(1-mean([PartCompactness(mg, part) for part in 1:num_parts]))
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

    #Log graph before any redistricting.
    LG.savegraph("before_graph_compressed", mg, compress=true)

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
    # initial_compactness = Compactness(mg)

    #Print before data.
    println("Number of vertices = ", LG.nv(mg))
    println("Connected? ", connected_before)
    println("Parity? ", parity_before)
    # println("Initial Compactness = ", Compactness(mg))
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
        # println("Initial Compactness = ", Compactness(mg))
        println("Dem percents before = ", dem_percent_before)
        println("Mean dem percent before = ", mean_dem_percent_before)
        println("Safe dem seats before = ", safe_dem_seats_before)


        println("**************After***************")
        # println("Final Score = ", ComponentScore(mg))
        println("Connected after? ", AllConnected(mg))
        println("Parity after? ", ParityCheckAll(mg))
        println("Parity after: ", DistanceToParity(mg))
        # println("Final Compactness = ", Compactness(mg))
        dem_percents_after = sort!(DemPercentages(mg))
        println("Target = ", target)
        println("Dem percents after = ", sort!(dem_percents_after))
        println("Mean dem percent after = ", mean(dem_percents_after))
        println("Safe dem seats after = ", SafeDemSeats(mg))
        if print_graph == true
            colors = PrintPartition(mg, locs_x, locs_y, name = "after.svg")
        end

        #Log graph after redistricting.
        LG.savegraph("after_graph_compressed.lgz", mg, compress=true)
    end
    println("Colors: ", enumerate(colors))

    return mg, G, colors
end

# mg, G = RePartition.RunFunc(print_graph = true, sim = true)

#Testing function for compactness measure.
function CompactnessTest(mg, part)
    # mg, G = InitialGraphPartition()
    part_nodes = MG.filter_vertices(mg, :part, part)
    points = [[MG.get_prop(mg, n, :pos)[1], MG.get_prop(mg, n, :pos)[2]] for n in part_nodes]
    ccave_hull = CH.concave_hull(points, 0)
    cvex_hull = CH.concave_hull(points, 10000)
    a = Plots.plot!(ccave_hull, show=true)
    b = Plots.plot!(cvex_hull, show=true)
    display(a)
    compactness = CH.area(ccave_hull) / CH.area(cvex_hull)
    return compactness
end

end

#Testing Code
import RePartition
mg, G, colors = RePartition.RunFunc(print_graph = true, sim = true)

# clf()
# Plots.plot()
# mg = MG.loadgraph("after_graph.lgz", MGFormat())
# for i in 1:RePartition.num_parts
#     compactness = RePartition.CompactnessTest(mg, i)
#     println("Compactness = ", compactness)
# end
