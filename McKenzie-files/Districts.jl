

mutable struct District
    pop::Int32
    dems::Int32
    reps::Int32
    tot::Int32
    dem_prop::Float64
    vtds::IntSet #Ordered list of nodes in the district.
end

#Calculate proportions of democratic votes in each district.
#Record in dictionary of district objects.
function UpdateDemProps(dist_dict)
    for part in keys(dist_dict)
        dist_dict[part].dem_prop = 100*(dist_dict[part].dems / dist_dict[part].tot)
    end
end

function CalculateDemPercentage(dist_dict, part)
    part_nodes = dist_dict[part].vtds
    part_tot = sum([MG.get_prop(mg, v, :tot) for v in part_nodes])
    part_dems = sum([MG.get_prop(mg, v, :dems) for v in part_nodes])
    return 100 * (part_dems / part_tot)
end

function DemPercentages(dist_dict)
    return [CalculateDemPercentage(dist_dict, part) for part in 1:num_parts]
end

function CreateDist(part_nodes)
    pop = sum([MG.get_prop(mg, v, :pop) for v in part_nodes])
    dems = sum([MG.get_prop(mg, v, :dems) for v in part_nodes])
    reps = sum([MG.get_prop(mg, v, :reps) for v in part_nodes])
    tot = sum([MG.get_prop(mg, v, :tot) for v in part_nodes])
    dem_prop = 100 * (dems / tot)
    vtds = IntSet(part_nodes)
    d = District(pop, dems, reps, tot, dem_prop, vtds)
    return d
end

function FindDistrictNum(dist_dict, node)
    for i in keys(dist_dict)
        if node in dist_dict[i].vtds
            return i
        end
    end

    #For testing only.
    println("Error: Node not found.")
    println("Node = ", node)
    println("Lengths = ", [length(dist_dict[i].vtds) for i in keys(dist_dict)])
    all_in_dist_dict = collect(Base.Iterators.flatten([dist_dict[i].vtds for i in keys(dist_dict)]))
    println("Length of all in dist_dict = ", length(all_in_dist_dict))
    diff = setdiff(1:MG.nv(mg), all_in_dist_dict)
    println("Difference: ", diff)
end
