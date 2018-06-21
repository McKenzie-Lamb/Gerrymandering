# Author: Abel Gonzalez
# Date: 06/05/18
#
# Description:
# This program takes the previously created network graph and
# transfrom it into a grid by adding the census tracts properties
# the number of nodes inside the graph can be changed by calling
# main function with a different value, this will not change the overall
# size of the function, more like the number of nodes contained in the 
# inside using graph_tool instead of networkx

import graph_tool.all as gt

grid = gt.lattice([10,10])

gt.graph_draw(grid, output="abel-network-files/images/tmp_grid.png")