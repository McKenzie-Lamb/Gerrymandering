"""
Author: Abel Gonzalez
Date: 10/11/18

Description:
Transform the networkx graph onto a map representation.
"""
import networkx as nx
import matplotlib.pyplot as plt
from descartes.patch import PolygonPatch


def main(filename):
    graph = nx.read_gpickle(filename)
    ax = plt.gca()
    ax.spines['top'].set_color('none')
    ax.spines['bottom'].set_color('none')
    ax.spines['left'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.set_aspect('equal', 'datalim')
    ax.tick_params(axis='both', labelcolor='none', color='none')
    count = 0
    for node in graph.nodes():
        count += 1
        for tract in graph.node[node]['polygon']:
            x, y = tract.exterior.xy
            plt.plot(x, y, color='none', zorder=1)
            patch = PolygonPatch(tract, facecolor='red', zorder=1)
            ax.add_patch(patch)
    plt.show()


main('whole_map_contig_point_adj.gpickle')
