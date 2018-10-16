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
include("Districts.jl")
include("Topology.jl")
include("Parity.jl")
include("Score.jl")
include("InitialPartition.jl")
include("Algorithm.jl")
include("PrintPartition.jl")


#Graph parameters
global mg = MG.MetaGraph()
const size = 1000
const num_parts = 18
const dem_mean = 0.5
const dem_sd = 0.5
const rand_graph = false
# const filename = "contig_16_share.gpickle" #Texas (incomplete data)
const filename = "pa_contiguos.gpickle" #Pennsylvania
# const filename = "whole_map_contig_point_adj.gpickle" # Wisconsin
global percent_dem = 50 #Default value.  Gets recalculated.
global par_thresh = 0.01

#Simulated annealing parameters
const safe_percentage = 55
global safe_seats = 9 #Placeholder.
#To win all but one seats for Democrats.
global target = append!([(num_parts*percent_dem-safe_percentage*safe_seats)/(num_parts - safe_seats) for i in 1:(num_parts - safe_seats)],
                 [safe_percentage for i in 1:safe_seats])
# global dem_target = sort([0.055, 0.135, 0.135, 0.135, 0.135, 0.135, 0.135, 0.135])

global dem_target = [1/num_parts for i in 1:num_parts] # Default value.

const max_moves = 4
const max_radius = 2
const max_tries = 10
bunch_radius = max_radius
const alpha = 0.95
const temperature_steps = 200
const T_min = alpha^temperature_steps
const max_swaps = 150
# const sa_steps = log(alpha, T_min)



function SafeDemSeats(mg)
    percentages = DemPercentages(mg)
    return length([p for p in percentages if p >= safe_percentage])
end


# @time PartitionDict(mg)
function RunFunc(;print_graph = false, sim = false)
    G, dist_dict = InitialGraphPartition()
    global mg
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
        colors = PrintPartition(dist_dict, locs_x, locs_y, name = "before.svg")
    end

    #Log graph before any redistricting.
    LG.savegraph("before_graph_compressed", mg, compress=true)

    # println("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    # dem_percents = sort!(DemPercentages(dist_dict))
    # println("Dem percents: ", sort!(dem_percents))
    # println("Parity: ", DistanceToParity(dist_dict))
    # # println("District Data: ", dist_dict)
    # println("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")


    #Record before data.
    # current_score = ComponentScore(mg)
    # println("Initial Score: ", current_score)
    connected_before = AllConnected(dist_dict)
    parity_before = ParityCheckAll(dist_dict)
    dem_percent_before = sort!(DemPercentages(dist_dict))
    mean_dem_percent_before = mean(dem_percent_before)
    safe_dem_seats_before = SafeDemSeats(dist_dict)
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
    println("Dem Target for Metis: ", dem_target)
    println("Initial Bunch Radius: ", bunch_radius)

    # for i in 1:10
    #     MoveCheck(mg)
    # end

    if sim == true
        @time dist_dict = SimulatedAnnealing(dist_dict)

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
        println("Connected after? ", AllConnected(dist_dict))
        println("Parity after? ", ParityCheckAll(dist_dict))
        println("Parity after: ", DistanceToParity(dist_dict))
        # println("Final Compactness = ", Compactness(mg))
        dem_percents_after = sort!(DemPercentages(dist_dict))
        println("Target = ", target)
        println("Dem percents after = ", sort!(dem_percents_after))
        println("Mean dem percent after = ", mean(dem_percents_after))
        println("Safe dem seats after = ", SafeDemSeats(dist_dict))
        if print_graph == true
            colors = PrintPartition(dist_dict, locs_x, locs_y, name = "after.svg")
        end

        #Log graph after redistricting.
        LG.savegraph("after_graph_compressed.lgz", mg, compress=true)
    end
    # println("Colors: ", enumerate(colors))

    return mg, G, dist_dict, colors
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
mg, G, dist_dict, colors = RePartition.RunFunc(print_graph = true, sim = true)

# clf()
# Plots.plot()
# mg = MG.loadgraph("after_graph.lgz", MGFormat())
# for i in 1:RePartition.num_parts
#     compactness = RePartition.CompactnessTest(mg, i)
#     println("Compactness = ", compactness)
# end
