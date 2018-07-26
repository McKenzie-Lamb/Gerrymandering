"""
Abel Gonzalez
07/11/18

MCMC algorithm implementation using networkx
"""
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
            with_labels=True, )
    plt.savefig(name + '.png')


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
            draw_graph(graph, subgraphs, 'tmp_main')

    return subgraphs, districts_data


def turn_off_edges(graph, districts_graphs, draw=False):
    """
    Turns off edges at randomly
    :param districts_graphs: the created subgraphs
    :param draw: true if you would like to draw the graphs at the end or false otherwise
    :return: dictionary with districts number as key and graph object as value
    """
    # turn on edges
    turned_off_graphs = dict()
    for i in districts_graphs.keys():
        turned_off_graphs[i] = districts_graphs[i].subgraph(districts_graphs[i].nodes()).copy()
        edges = districts_graphs[i].edges()
        # no_edges_to_change = random.randint(len(edges)//2, 3*len(edges)//4)  # probability of number of edges
        turned_off = random.sample(edges, 2*len(edges) // 3)
        turned_off_graphs[i].remove_edges_from(turned_off)

    if draw:
        draw_graph(graph, turned_off_graphs, 'turned_off')
    return turned_off_graphs


def gather_connected_components(graph, turned_off_graphs, districts_graphs):
    """
    Uses the graphs with edges turned off and gather all of the connected components that are in the boundaries
    :param graph: main graph
    :param turned_off_graphs: the graph with turned off edges
    :param districts_graphs: graph views of main graph
    :return: (dict) connected component along boundaries, keys are the nodes and value the neighboring district
    """
    connected_components = dict()
    for i in turned_off_graphs.keys():
        connected_components[i] = nx.connected_components(turned_off_graphs[i])
    components_dict_add = {i: [] for i in connected_components.keys()}  # components and districts associated with
    components_dict_delete = {i: [] for i in connected_components.keys()}
    components_check = []
    for district in connected_components.keys():
        outside_districts_nodes = {i: list(districts_graphs[i].nodes) for i in districts_graphs.keys() if i != district}
        for component in connected_components[district]:
            if list(component) in components_check:
                continue
            for outside_district in outside_districts_nodes.keys():
                if len(nx.node_boundary(graph, component, outside_districts_nodes[outside_district])) == len(component):
                    components_check.append((list(component)))
                    components_dict_add[outside_district].append(list(component))
                    components_dict_delete[district].append(list(component))
                    break
    components_dict_add, components_dict_delete = _reduce_connected_components(components_dict_add, components_dict_delete)
    return [components_dict_add, components_dict_delete]


def _reduce_connected_components(components_dict_add, components_dict_delete):
    new_components_dict_add = {i: [] for i in components_dict_add.keys()}
    new_components_dict_delete = {i: [] for i in components_dict_delete.keys()}
    for i in components_dict_add:
        sample = random.sample(components_dict_add[i], len(components_dict_add[i])//2)
        new_components_dict_add[i] = [node for component in sample for node in component]
        for j in components_dict_delete.keys():
            for c in components_dict_delete[j]:
                if c in sample:
                    new_components_dict_delete[j].append(c)
    for i in new_components_dict_delete.keys():
        new_components_dict_delete[i] = [node for component in new_components_dict_delete[i] for node in component]
    return new_components_dict_add, new_components_dict_delete


def propose_swap(graph, districts_graphs, selected_components, districts_data, filename, swaps, draw=False):
    new_districts_graphs = dict()
    new_districts_data = copy.deepcopy(districts_data)
    for district in districts_graphs.keys():
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
                    print('Pop disparity')
                    return districts_graphs, districts_data, swaps
            else:
                print('Discontinuous graph')
                return districts_graphs, districts_data, swaps
        except KeyError:
            if nx.is_connected(new_districts_graphs[i]):
                continue
            else:
                return districts_graphs, districts_data, swaps
    districts_graphs = copy.deepcopy(new_districts_graphs)
    districts_data = copy.deepcopy(new_districts_data)
    swaps += 1
    if draw:
        draw_graph(graph, districts_graphs, filename)
    return districts_graphs, districts_data, swaps


def main(graph_file_name, total_no_districts, swaps_to_try):
    """
    Main function to run the algorithm
    :param graph_file_name: the name of the file that we want to import
    :param total_no_districts: total number of districts desired
    :return None
    """
    # Create paths
    data_folder = path.Path("./data/")
    images_folder = path.Path("./images/")
    print('Initializing...')
    # Load the graph
    graph = nx.read_gpickle(graph_file_name)

    # create partitions using metis
    districts_graphs, districts_data = separate_graphs(graph, total_no_districts, draw=False)
    actual_swaps = 0
    # gather connected components in boundaries
    print('Swapping...')
    start = time.time()
    for i in range(swaps_to_try):
        turned_off_graphs = turn_off_edges(graph, districts_graphs)
        connected_components = gather_connected_components(graph, turned_off_graphs, districts_graphs)
        districts_graphs, districts_data, actual_swaps = propose_swap(graph, districts_graphs, connected_components,
                                                                      districts_data, str(i), actual_swaps, draw=False)
    end = time.time()

    print('DONE')
    print('Statistics:')
    print('-----------')
    print('Swaps:', swaps_to_try, '-', actual_swaps)
    print('Time:', end - start)

main('tmp_graph100.gpickle', 4, 10)

