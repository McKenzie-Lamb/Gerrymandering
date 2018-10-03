#Functions for the RePartition module related to topology.

function InteriorBoundary(nodes)
    exterior_bdy = Boundary(nodes)
    b_list = IntSet()
    for v in exterior_bdy
        union!(b_list, LG.neighbors(mg, v))
    end
    b_list = intersect(b_list, nodes)
    return b_list
end

#Returns the exterior node boundary of the set "nodes" within the graph "mg".
#Translated from NetworkX
function Boundary(nodes)
    b_list = IntSet()
    for v in nodes
        union!(b_list, LG.neighbors(mg, v))
    end
    setdiff!(b_list, nodes)
    return b_list
end

function PartConnected(dist_dict, part)
    part_nodes = collect(dist_dict[part].vtds)
    subgraph, vm = LG.induced_subgraph(mg, part_nodes)
    return LG.is_connected(subgraph)
end

#Returns true if all districts are connected, false otherwise.
function AllConnected(dist_dict)
    connected = true
    for part in 1:num_parts
        if !PartConnected(dist_dict, part)
            connected = false
            break
        end
    end
    return connected
end

#Checks whether district part_from would be connected if the nodes in
#bunch_to_move were removed.  Returns true or false.
function CheckConnectedWithoutBunch(dist_dict, part_from, bunch_to_move)
    part_nodes = setdiff(dist_dict[part_from].vtds, bunch_to_move)
    subgraph, vm = LG.induced_subgraph(mg, collect(part_nodes))
    return LG.is_connected(subgraph)
end

function PartCompactness(dist_dict, part)
    part_nodes = dist_dict[part].vtds
    points = [[MG.get_prop(mg, n, :pos)[1], MG.get_prop(mg, n, :pos)[2]] for n in part_nodes]
    ccave_hull = CH.concave_hull(points, 0)
    cvex_hull = CH.concave_hull(points, 10000)
    compactness = CH.area(ccave_hull) / CH.area(cvex_hull)
    return compactness
end

function Compactness(dist_dict)
    return 100*(1-mean([PartCompactness(dist_dict, part) for part in 1:num_parts]))
end
