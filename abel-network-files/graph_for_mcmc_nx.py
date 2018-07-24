"""
Abel Gonzalez
07/11/18

Creates a delaunay graph to be used by mcmc netyworkx file
"""

import scipy.spatial
import random
import networkx as nx
import matplotlib.pyplot as plt

# random points to be used
nodes = [i for i in range(100)]
points = [(random.uniform(0,100),random.uniform(0,100)) for i in range(len(nodes))]

# make a Delaunay triangulation of the point data
t = scipy.spatial.Delaunay(points)

# create a set for edges that are indexes of the points
edges = []
m = dict(enumerate(nodes))

for i in range(t.nsimplex):
    edges.append((m[t.vertices[i, 0]], m[t.vertices[i, 1]]))
    edges.append((m[t.vertices[i, 1]], m[t.vertices[i, 2]]))
    edges.append((m[t.vertices[i, 2]], m[t.vertices[i, 0]]))

# make a graph based on the Delaunay triangulation edges
graph = nx.Graph(directed=False)
graph.graph['positions'] = points
graph.add_nodes_from(nodes)
graph.add_edges_from(edges)
pos = dict(zip(nodes, points))
nx.draw(graph,pos)

# populate the graph with random values
for i in graph.nodes():
    pop = random.randint(500,2000)
    rep = random.randint(0,pop)
    dem = pop - rep
    graph.nodes[i]['pop'] = pop
    graph.nodes[i]['rep'] = rep
    graph.nodes[i]['dem'] = dem
# save graph to file
print(graph.node[23]['pop'])
nx.write_gpickle(graph, 'tmp_graph100.gpickle')

