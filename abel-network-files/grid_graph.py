import graph_tool.all as gt
import time
x_total_ver = 200
y_total_ver = 200

def get_position(x,y):

    y = y*-1
    old_min_x = 298550.4294446295
    old_max_x = 766195.0569210261
    old_range_x = old_max_x - old_min_x

    old_min_y =225691.9025871229
    old_max_y = 723701.7170331448
    old_range_y = old_max_y - old_min_y

    new_max = 100
    new_min = 0
    new_range = new_max - new_min
    new_x = (((x - old_min_x) * new_range)/old_range_x)
    new_y = (((y - old_min_y) * new_range)/old_range_y)

    return (new_x,new_y)
print("Creating...")
start = time.time()
positions = []
for i in range(x_total_ver):
    for j in range(y_total_ver):

        positions.append(get_position(i,j))

grid = gt.lattice([x_total_ver,y_total_ver])

pos = grid.new_vertex_property("vector<double>")

index = 0
for vertex in grid.vertices():
    pos[vertex] = positions[index]
    index+=1
end = time.time()
print(end-start)
print("Drawing...")
gt.graph_draw(
              grid, pos=pos, output_size=(3000,3000),
              output="abel-network-files/images/tmp_grid.png") 