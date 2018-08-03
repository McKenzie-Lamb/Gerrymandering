import time
import copy
import math
import path
import metis
import random
import networkx as nx
import matplotlib.pyplot as plt



def draw_graph(graph, districts_graphs, name):
    """
    Draw a graph using the matplotlib module
    :param graph: networkx graph to be drawn
    :param districts_graphs: dictionary with graphs
    :return: None
    """
    colors = ['lightpink', 'yellow', 'lime', 'cyan', 'purple', 'slategray', 'peru']
    for i in districts_graphs.keys():
        for n in districts_graphs[i].nodes():
            graph.node[n]['color'] = colors[i]
    nx.draw(graph, pos=graph.graph['positions'], node_color=[graph.node[i]['color'] for i in graph.nodes()],
            with_labels=False, node_size=100)
    plt.savefig(name+'.png')


def separate_graphs(graph, total_no_districts, draw=False):
    """
    Uses the metis package to separate graphs into districts partitions
    :param graph: networkx graph to be partitioned
    :param total_no_districts: the total number of districts desired
    :param draw: (optional) if you would like to draw the graph of different districts
    :return:list of subgraphs
    """

    graph.graph['node_weight_attr'] = 'pop'
    metis_graph = metis.networkx_to_metis(graph)
    objval, parts = metis.part_graph(metis_graph, contig=True, nparts=total_no_districts)

    subgraphs_nodes = {p: [] for p in parts}
    districts_data = {p: [0, 0, 0] for p in parts}
    for index, district in enumerate(parts):
        subgraphs_nodes[district].append(index)
        districts_data[district][0] += graph.nodes[index]['pop']
        districts_data[district][1] += graph.nodes[index]['dem']
        districts_data[district][2] += graph.nodes[index]['rep']

    subgraphs = dict()
    for i in subgraphs_nodes.keys():
        subgraphs[i] = graph.subgraph(subgraphs_nodes[i])

    if draw:
        colors = ['lightpink', 'yellow', 'lime', 'cyan', 'purple', 'slategray', 'peru']
        for i in subgraphs.keys():
            for n in subgraphs[i].nodes():
                graph.node[n]['color'] = colors[i]
            draw_graph(graph, subgraphs, 'main')

    return subgraphs, districts_data


def select_nodes_to_swap(graph, districts_graphs):
    add_nodes = dict()
    del_nodes = dict()

    track_list = []
    random_district = random.randint(0, len(districts_graphs)-1)
    for j in range(100):
        if random_district in track_list:
            break
        #print(districts_graphs)
        boundary_node = random.sample(nx.node_boundary(graph, districts_graphs[random_district]), 1)
        add_nodes[random_district] = boundary_node
        for i in districts_graphs.keys():
            if boundary_node[0] in districts_graphs[i]:
                del_nodes[i] = boundary_node
                track_list.append(random_district)
                random_district = i
                break
    #print(add_nodes, del_nodes)
    return [add_nodes, del_nodes]


def propose_swap(graph, districts_graphs, districts_data):
    selected_components = select_nodes_to_swap(graph, districts_graphs)
    new_districts_graphs = dict()
    new_districts_data = copy.deepcopy(districts_data)
    for district in districts_graphs.keys():
        if district not in selected_components[0] or district not in selected_components[1]:
            new_districts_graphs[district] = nx.subgraph(graph, districts_graphs[district].nodes())
            continue
        new_districts_nodes = set(selected_components[0][district]) | set(districts_graphs[district].nodes())
        new_districts_nodes -= set(selected_components[1][district])
        new_districts_graphs[district] = nx.subgraph(graph, list(new_districts_nodes))
        new_districts_data[district][0] += sum([graph.node[i]['pop'] for i in selected_components[0][district]])
        new_districts_data[district][0] -= sum([graph.node[i]['pop'] for i in selected_components[1][district]])
        new_districts_data[district][1] += sum([graph.node[i]['dem'] for i in selected_components[0][district]])
        new_districts_data[district][1] -= sum([graph.node[i]['dem'] for i in selected_components[1][district]])
        new_districts_data[district][2] += sum([graph.node[i]['rep'] for i in selected_components[0][district]])
        new_districts_data[district][2] -= sum([graph.node[i]['rep'] for i in selected_components[1][district]])
    for i in new_districts_graphs.keys():
        # check that current and following district has same pop, the excepts handling is in case of getting to the last
        # value
        try:
            if nx.is_connected(new_districts_graphs[i]):
                if math.isclose(new_districts_data[i][0],new_districts_data[i + 1][0], rel_tol=0.20):
                    continue
                else:
                    #print('Pop disparity')
                    return districts_graphs, districts_data
            else:
                #print('Discontinuous graph')
                return districts_graphs, districts_data
        except KeyError:
            if nx.is_connected(new_districts_graphs[i]):
                continue
            else:
                return districts_graphs, districts_data
    return new_districts_graphs, new_districts_data

def total_dem(data):
    goals = sorted([40, 40, 40, 40])
    current_values = sorted([data[district][1]/data[district][0]*100 for district in data.keys()])
    score = sum(abs(i-j) for i, j in zip(current_values, goals))
#    print("Score: ", score)
    return score


def _acceptance_prob(old_cost, new_cost, T):
    ap = math.e * ((old_cost-new_cost)/T)
    if ap > 1:
        return 1
    else:
        return ap


def anneal(districts_data, graph, districts_graphs):
    old_cost = total_dem(districts_data)
    print("Initial Cost: ", old_cost)
    print("Initial Dem Percents: ", )
    T = 1.0
    T_min = 0.00001
    alpha = 0.8
    swaps = [100, 0]
    while T > T_min:
        i = 1
        while i <= swaps[0]:
            new_districts_graphs, new_districts_data = propose_swap(graph, districts_graphs, districts_data)
            new_cost = total_dem(new_districts_data)
            ap = _acceptance_prob(old_cost, new_cost, T)
            if ap > random.random():
                print("Score: ", new_cost)
                swaps[1] += 1
                districts_graphs = copy.deepcopy(new_districts_graphs)
                districts_data = copy.deepcopy(new_districts_data)
                old_cost = new_cost
            i += 1
        T = T*alpha
    return new_districts_graphs, new_districts_data, swaps


def main(graph_file_name, total_no_districts):
    data_folder = path.Path("./data/")
    images_folder = path.Path("./images/")
    print('Initializing...')
    # Load the graph
    graph = nx.read_gpickle(graph_file_name)

    # create partitions using metis
    districts_graphs, districts_data = separate_graphs(graph, total_no_districts, draw=False)
    start_dem = districts_data
    # gather connected components in boundaries
    print('Swapping...')
    start = time.time()
    new_districts_graphs, new_districts_data, swaps = anneal(districts_data, graph, districts_graphs)
    end = time.time()
#    draw_graph(graph, new_districts_graphs, 'end')
    end_dem = new_districts_data
    print('DONE')
    print('Statistics:')
    print('-----------')
    print('Swaps', swaps[0], '-', swaps[1])
    print('Dem Change', start_dem, end_dem)
    print('Time:', end - start)

main('tmp_graph1000.gpickle', 4)