# using LightGraphs; LG = LightGraphs
# using MetaGraphs; MG = MetaGraphs

# module Districts
#
# export District
# export DistrictSet

mutable struct District
    pop::Int
    dems::Int
    dem_prop::Float64

    # function District(;pop = 0, dems = 0, dem_prop = 0)
end

# struct DistrictSet
#     district_dict::Dict{Int,District}
#     target::Dict{Int, Float64}
# end


# end
