#=Creates the initial graph and partition using Metis (via Python)=#
#Create a randomly generated graph and partition it using Metis (via Python)
function InitialGraphPartition()
    #Global variables to be updated based on graph data.
    global target
    global percent_dem

    #Import partitioned graph from Python/Metis.
    G, parts = RPG.MakeGraphPartition(size = size, num_parts = num_parts,
            dem_sd = dem_sd, filename = filename, rand_graph = rand_graph,
            target = dem_target)

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
        total = MG.get_prop(mg, v, :dems) + MG.get_prop(mg, v, :reps)
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
    # target = [32, 54, 54, 54, 54, 54, 54, 54]
    # target = [28.1597, 53.6469, 54.06, 54.1618, 54.2257, 54.3312, 54.5771, 54.883]
    target = append!([num_parts*percent_dem-safe_percentage*(num_parts - 1)],
                    [safe_percentage for i in 1:(num_parts - 1)])
    #sort([53.8291, 53.82, 53.7211, 31.523, 53.7479, 53.8298, 53.7259, 53.51])

    return mg, G
end
