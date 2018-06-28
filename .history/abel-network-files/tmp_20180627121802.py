import numpy as np
import graph_tool.all as gt

size_array = np.random.random([50, 2])
graph, pos = gt.triangulation(size_array, type='delaunay')

u = gt.GraphView(graph, vfilt=(1,2,3))

gt.graph_draw(graph, pos, output="abel-network-files/tmp_alg.png", bg_color=(255,255,255,1))