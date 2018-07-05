import graph_tool.all as gt

g = gt.Graph(directed = False)

g.add_vertex(10)

color = g.new_vertex_property('vector<float>')

for i in g.vertices():
    color[i] = (1,1,1,1)

gt.graph_draw(g, vertex_fill_color = color)