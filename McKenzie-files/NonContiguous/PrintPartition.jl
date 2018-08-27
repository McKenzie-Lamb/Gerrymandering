using Colors
using LightGraphs; LG = LightGraphs
using MetaGraphs; MG = MetaGraphs
using GraphPlot, Compose
GP = GraphPlot

function EdgeColor(mg, edge)
    src_part = MG.get_prop(mg, LG.src(edge), :part)
    dst_part = MG.get_prop(mg, LG.dst(edge), :part)
    if src_part == dst_part
        return colorant"black"
    else
        return colorant"lightgrey"
    end

end

function PrintPartition(mg, locs_x, locs_y; name = "partition.svg", filename = "small_map_no_discontiguos.gpickle")
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
    Compose.draw(SVG(name, 16cm, 16cm), GP.gplot(mg, locs_x, locs_y,
        nodefillc=nodefillc, nodestrokelw = nodestrokelw,
        nodestrokec = nodestrokec, edgestrokec=edgestrokec,
        NODESIZE = NODESIZE))
    return colors
end
