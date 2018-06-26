# Author: Abel Gonzalez
# Date: 06/18/18
#
# Description:
# This program uses the .shp file to create a network graph where each node represents a census tract
# and the edge represents adjacency between each tract, usign graph-tool instead of networkx

import graph_tool.all as gt
from pathlib import Path

data_folder = Path("abel-network-files/data/")
images_folder = Path("abel-network-files/images/")

graph = gt.load_graph(str(data_folder / "tmp_graph.gt"))