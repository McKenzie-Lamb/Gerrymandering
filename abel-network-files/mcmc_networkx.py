"""
Abel Gonzalez
07/11/18

MCMC algorithm implementation using networkx
"""

import path
import metis
import random
import networkx as nx
import matplotlib.pyplot as plt


def draw_graph(graph, districts_graphs):
    """
    Draw a graph using the matplotlib module
    :param graph: networkx graph to be drawn
    :return: None
    """
    colors = ['lightpink', 'yellow', 'lime', 'cyan', 'purple', 'slategray', 'peru']
    for i in districts_graphs.keys():
        for n in districts_graphs[i].nodes():
            graph.node[n]['color'] = colors[i]
    nx.draw(graph, pos=graph.graph['positions'], node_color=[graph.node[i]['color'] for i in graph.nodes()],
            with_labels=True)
    plt.show()

def separate_graphs(graph, total_no_districts, draw=False, verbose=False):
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
    colors = ['lightpink', 'yellow', 'lime', 'cyan', 'purple', 'slategray', 'peru']

    subgraphs_nodes = {p: [] for p in parts}
    district_populations = {p: 0 for p in parts}
    for index, district in enumerate(parts):
        subgraphs_nodes[district].append(index)
        district_populations[district] += graph.nodes[index]['pop']

    subgraphs = dict()
    for i in subgraphs_nodes.keys():
        subgraphs[i] = graph.subgraph(subgraphs_nodes[i])

    if verbose:
        print('Districts population:', district_populations)

    if draw:
        colors = ['lightpink', 'yellow', 'lime', 'cyan', 'purple', 'slategray', 'peru']
        for i in subgraphs.keys():
            for n in subgraphs[i].nodes():
                graph.node[n]['color'] = colors[i]
            draw_graph(graph, subgraphs)

    return subgraphs


def turn_off_edges(districts_graphs, draw=False):
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
        #no_edges_to_change = random.randint(len(edges)//2, 3*len(edges)//4)  # probability of number of edges
        turned_off = random.sample(edges, 5*len(edges)//6)
        turned_off_graphs[i].remove_edges_from(turned_off)

    if draw:
        for i in districts_graphs.keys():
            draw_graph(turned_off_graphs[i])
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
            skip = random.randint(1,4)
            if list(component) in components_check:
                continue
            if skip < 4:
                continue
            for outside_district in outside_districts_nodes.keys():
                if len(nx.node_boundary(graph, component, outside_districts_nodes[outside_district])) > 0:
                    components_check.append((list(component)))
                    components_dict_add[outside_district]+=(list(component))
                    components_dict_delete[district]+=(list(component))
                    break

    print(components_dict_add)
    print(components_dict_delete)
    return [components_dict_add, components_dict_delete]


def propose_swap(graph, districts_graphs, selected_components, draw=False):
    new_districts_graphs = dict()
    for district in districts_graphs.keys():
        new_districts_nodes = set(selected_components[0][district]) | set(districts_graphs[district].nodes())
        new_districts_nodes -= set(selected_components[1][district])
        new_districts_graphs[district] = nx.subgraph(graph, new_districts_nodes)

    if draw:
        draw_graph(graph, new_districts_graphs)
    return districts_graphs

def main(graph_file_name, total_no_districts):
    """
    Main function to run the algorithm
    :param graph_file_name: the name of the file that we want to import
    :param total_no_districts: total number of districts desired
    :return None
    """
    # Create paths
    data_folder = path.Path("./data/")
    images_folder = path.Path("./images/")

    # Load the graph
    graph = nx.read_gpickle(graph_file_name)

    # create partitions using metis
    districts_graphs = separate_graphs(graph, total_no_districts, draw=True, verbose=True)

    # gather connected components in boundaries
    turned_off_graphs = turn_off_edges(districts_graphs, draw=False)
    connected_components = gather_connected_components(graph, turned_off_graphs, districts_graphs)
    propose_swap(graph, districts_graphs, connected_components, draw=True)

main('tmp_graph1100.gpickle', 3)
