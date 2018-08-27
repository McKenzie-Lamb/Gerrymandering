using Colors
using PyCall
using LightGraphs; LG = LightGraphs
using MetaGraphs; MG = MetaGraphs
using GraphPlot, Compose
GP = GraphPlot
using Plots; pyplot(reuse=false)
using PyPlot
using ConcaveHull; CH = ConcaveHull
cd(dirname(Base.source_path()))
println(pwd())
include("Districts.jl")
# include("RePartition.jl")
import RePartition; RP = RePartition

function PrintPart(mg, locs_x, locs_y)
    num_parts = MG.get_prop(mg, :num_parts)
    colors = distinguishable_colors(num_parts)
    # symbols = ["A", "B", "C", "D"]
    verts = LG.vertices(mg)
    partition = [MG.get_prop(mg, v, :part) for v in MG.vertices(mg)]
    dem_colors = Colors.colormap("RdBu")
    # println([floor(round(100*round(MG.get_prop(mg, v, :dems)/MG.get_prop(mg, v, :pop),2)))
            # for v in MG.vertices(mg)])
    # dem_props = [max(1, Int(floor(round(100*round(MG.get_prop(mg, v, :dems)/MG.get_prop(mg, v, :pop),2)))))
                # for v in MG.vertices(mg)]
    NODESIZE = 50/LG.nv(mg)
    NODELABELSIZE = 1.0
    # nodefillc = [dem_colors[prop] for prop in dem_props]
    # print(nodefillc)
    # nodelabel = [symbols[p] for p in partition]
    # nodelabelsize = 0.00001
    # print(length(nodefillc))
    nodesize = [MG.get_prop(mg, v, :dems) for v in LG.vertices(mg)]
    edgestrokec = [EdgeColor(mg, edge) for edge in LG.edges(mg)]
    nodestrokelw = 2/LG.nv(mg)
    # nodestrokec = [dem_colors[prop] for prop in dem_props]
    nodefillc = colors[partition]
    # nodefillc = nodestrokec
    nodestrokec = colorant"lightgray" #colors[partition]

end


mg = MG.loadgraph("after_graph.lgz", MGFormat())
part_nodes = MG.filter_vertices(mg, :part, 3)
points = [[MG.get_prop(mg, n, :pos)[1], MG.get_prop(mg, n, :pos)[2]] for n in part_nodes]
sub_graph, vm = LG.induced_subgraph(mg, collect(part_nodes))
# for edge in LG.edges(sub_graph)
#     src = LG.src(edge)
#     dst = LG.dst(edge)
#     src_pos = MG.get_prop(mg, src, :pos)
#     dst_pos = MG.get_prop(mg, dst, :pos)
#     x = (src_pos[1]+dst_pos[1])/2
#     y = (src_pos[2]+dst_pos[2])/2
#     midpt = [x,y]
#     # println(midpt)
#     push!(points, midpt)
# end
ccave_hull = CH.concave_hull(points, 0)
cvex_hull = CH.concave_hull(points, 10000)
clf()
a = plot(ccave_hull)
b = plot(cvex_hull)
locs_x = [v[1] for v  in points]
locs_y = [-v[2] for v  in points]
plot(draw(SVG("convex_hull_example.svg"), GP.gplot(sub_graph, locs_x, locs_y)))
display(a)
