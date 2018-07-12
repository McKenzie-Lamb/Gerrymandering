import numpy as np
import graph_tool.all as gt

size_array = np.random.random([50, 2])
size = np.random.random(50)
graph, pos = gt.triangulation(size_array, type='delaunay')

graph.vp.pos = pos
matched_vertices = gt.find_vertex(graph, pos, (0,0))

u = gt.GraphView(graph, vfilt=size)

gt.graph_draw(u, pos, output="abel-network-files/tmp_alg.png", bg_color=(255,255,255,1))