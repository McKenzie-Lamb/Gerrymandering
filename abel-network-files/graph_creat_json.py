import json
import math
import networkx as nx
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.geometry import Point


def read_json(filename):
    '''Read the .json file with the data

    Arguments:
        filename {str} -- filename and path

    Returns:
        dict -- dicitonary with geoid as keys and precints data as values
    '''
    print("Reading .json...")
    with open(filename) as json_data:
        map_data = json.load(json_data)
    return map_data


def get_rlist(geo):
    '''Extracts the coordinates from the file, if it is a Polygon add an extra
    bracket for make all data the same

    Arguments:
        geo {dict} -- dictionary with type and coordinates keys

    Returns:
        list -- list of list of each rlist
    '''
    if geo['type'] == "Polygon":
        rings = geo['coordinates']
        rlist = [rings]
    elif geo['type'] == "MultiPolygon":
        rlist = geo['coordinates']
    return rlist


def get_poly(rings):
    '''Creates the polygons using shapely

    Arguments:
        rings {list} -- list with the points coordinates

    Returns:
        list -- [0] is the list of polygons, [1] the list of areas
    '''
    tracts = []
    area = 0
    for points in rings:
        ptlst = list(points)
        # In case there are not enough points to create a polygon
        if ptlst is None or len(ptlst) < 3:
            print("BAD!")
            continue
        poly = Polygon(ptlst)
        area += poly.area * 10000
        tracts += [poly]
    return tracts, area


def get_position(tracts):
    '''Gets the x and y center positions by averaging the center positions of
    each polygon

    Arguments:
        tracts {list} -- list of coordinates

    Returns:
        list -- [0] center at x [1] center at y
    '''
    centerx = 0
    centery = 0
    for i in tracts:
        x = i.centroid.x
        y = i.centroid.y
        centerx += x
        centery += y
    return centerx/len(tracts), centery/len(tracts)


def normalize_voting_data(data):
    '''Normalizes the data by changing votes for each party dependent on the
    share from the total votes they represent.

    Arguments:
        data {dict} -- dictionary with voting data

    Returns:
        list -- list with the new values for [0] population [1] democrats
        [2] republicans
    '''
    try:
        dem_share = int(data['dem'])/(int(data['dem'])+int(data['rep']))
    except ZeroDivisionError:
        dem_share = .5
    dem = math.floor(int(data['pop'])*dem_share)
    rep = int(data['pop'])-dem
    return [data['pop'], dem, rep]


def is_adjacent(shape1, shape2):
    return shape1.touches(shape2) and not isinstance(
        shape1.intersection(shape2), Point)


def positions_to_graph(graph):
    positions = dict()
    for i in graph.nodes():
        positions[i] = (graph.node[i]['pos'])
    return positions


def clean_graph(graph):
    print("Cleaning...")
    nodes_to_del = []
    for i in nx.connected_components(graph):
        if len(i) < 27:
            for j in i:
                nodes_to_del.append(j)
    graph.remove_nodes_from(nodes_to_del)
    return graph


def create_graph(map_data):
    graph = nx.Graph(directed=False)
    count = 0
    print("Creating Graph...")
    for precinct in map_data:
        geoid = precinct

        # Getting the coordinates from file based on Polygon and Multypolygon
        try:
            rlist = get_rlist(map_data[precinct]['geo'])
        except KeyError:  # In three ocations the data is messed up
            continue
        tracts = []
        area = 0
        for rings in rlist:
            tracts += get_poly(rings)[0]
            area += get_poly(rings)[1]

        positionx, positiony = get_position(tracts)
        normalized_votes = normalize_voting_data(map_data[precinct])
        graph.add_node(geoid, polygon=tracts, pop=normalized_votes[0],
                       dem=normalized_votes[1], rep=normalized_votes[2],
                       pos=(positionx, positiony), area=area)
        latest_node = list(graph.nodes(data=False))[-1]
        for n in list(graph.nodes())[:count-1]:
                for i in graph.node[n]['polygon']:
                    for j in graph.node[latest_node]['polygon']:
                        if is_adjacent(i, j):
                            graph.add_edge(n, latest_node)
    positions = positions_to_graph(graph)
    graph.graph['positions'] = positions
    graph = clean_graph(graph)
    return graph


map_data = read_json('data/data.json')
graph = create_graph(map_data)
print('Drawing Graph...')
nx.draw(graph, graph.graph['positions'], node_size=(10))
nx.write_gpickle(graph, 'pa_contiguos.gpickle')
plt.savefig('tmp', dpi=300)