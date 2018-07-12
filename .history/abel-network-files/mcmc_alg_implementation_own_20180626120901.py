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

# Loading the previous created Graph.
graph = gt.load_graph(str(data_folder / "tmp_graph.gt"))

districts = gt.minimize_blockmodel_dl(graph, 2,2)
r  = districts.get_blocks()
swap = districts.add_vertex(int(9))


districts.draw(pos=graph.vp.pos,vertex_text=graph.vertex_index, output='abel-network-files/tmp.png')