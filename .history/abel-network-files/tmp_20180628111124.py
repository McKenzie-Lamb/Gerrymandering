# Author: Abel Gonzalez
# Date: 06/26/18
#
# Description:
# This program uses the .shp file to create a network graph where each node
# represents a census tract and the edge represents adjacency between each
# tract, usign graph-tool instead of networkx
import random
import graph_tool.all as gt
from pathlib import Path

#def turned_on_edges():

    

# Paths
data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

# Loading the previous created Graph and creating the prop maps
graph = gt.load_graph(str(data_folder / "tmp_graph.gt"))
color = graph.new_vertex_property("vector<double>")
ring_color = graph.new_vertex_property("vector<double>")
district_no = graph.new_vertex_property("int")

# Separates graph into blocks
districts = gt.minimize_blockmodel_dl(graph, 2,2)
blocks = districts.get_blocks()

print(blocks[1])

