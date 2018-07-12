# Author: Abel Gonzalez
# Date: 06/26/18
#
# Description:
# This program uses the .shp file to create a network graph where each node
# represents a census tract and the edge represents adjacency between each
# tract, usign graph-tool instead of networkx

import graph_tool.all as gt
from pathlib import Path

# Paths
data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

# Loading the previous created Graph and creating the prop maps
graph = gt.load_graph(str(data_folder / "tmp_graph.gt"))
district_no = graph.new_vertex_property("int")
color = graph.new_vertex_property("vector<double>")

# Assigning the district to each vertex as a property map
districts = gt.minimize_blockmodel_dl(graph, 2,2)
blocks = districts.get_blocks()
for i in graph.vertices():
    district_no[graph.vertex(i)] = blocks[i]
    color = (255, 0, 0, 1) if blocks[i] = 1 else (0,0,255,1)


gt.graph_draw(graph, bg_color = (255,255,255,1), vertex_color=color, pos=graph.vp.pos,vertex_text=graph.vertex_index, output='abel-network-files/tmp.png')