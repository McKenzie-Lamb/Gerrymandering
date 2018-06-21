#%%
import graph_tool.all as gt

#%%
g = gt.Graph()
ug = gt.Graph(directed=False)

v1 = g.add_vertex()
v2 = g.add_vertex()

e = g.add_edge(v1, v2)

gt.graph_draw(g, vertex_text=g.vertex_index, vertex_font_size = 18, output_size=(200,200), output="abel-network-files/images/two-nodes.png")

#%%
vlist = g.add_vertex(10)
print(len(list(vlist)))

v = g.add_vertex()
print(g.vertex_index[v])

print(int(v))

g.remove_edge(e)
g.remove_vertex(v2)
gt.graph_draw(g, vertex_text=g.vertex_index, vertex_font_size = 18, output_size=(200,200), output="abel-network-files/images/two-nodes.png")

v = g.vertex(8)
print(v)

