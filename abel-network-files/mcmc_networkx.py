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


def draw_graph(graph):
    """
    Draw a graph using the matplotlib module
    :param graph: networkx graph to be drawn
    :return: None
    """
    nx.draw(graph, pos=graph.graph['positions'], node_color=[graph.node[i]['color'] for i in graph.nodes()],
            with_labels=True)


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
            draw_graph(subgraphs[i])
        plt.show()
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
        plt.show()
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

    components_dict = dict() # components and districts associated with
    for district in connected_components.keys():
        outside_districts_nodes = {district: list(districts_graphs[i].nodes) for i in range(len(districts_graphs)) if i != district}
        for component in connected_components[district]:
            for outside_district in outside_districts_nodes.keys():
                if len(nx.node_boundary(graph, component, outside_districts_nodes[outside_district])) > 0:
                    components_dict[tuple(component)] = outside_district
    print(random.sample(list(components_dict), 1*len(components_dict)//5))
    return components_dict


#def propose_swap():



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
    turned_off_graphs = turn_off_edges(districts_graphs, draw=True)
    connected_components = gather_connected_components(graph, turned_off_graphs, districts_graphs)
    propose_swap()

main('tmp_graph1100.gpickle', 2)
