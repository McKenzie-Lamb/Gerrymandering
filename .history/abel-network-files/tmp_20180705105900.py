import graph_tool.all as gt

g = gt.Graph(directed = False)

g.add_vertex(10)

color = g.new_vertex_property('vector<float>')

for i in g.vertices():
    color[i] = [0.1,0.1,0.1]
g.vp.color = color

gt.graph_draw(g, vertex_fill_color = g.vp.color)