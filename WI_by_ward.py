# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 13:08:46 2017

@author: wr
"""

import matplotlib.pyplot as plt
from descartes.patch import PolygonPatch

from  shapely.geometry import Polygon

import fiona

def contacts(p1, p2):
    (x11,y11,x12,y12) = p1.bounds
    (x21,y21,x22,y22) = p2.bounds
    if x11>x22 or x21 > x12 or y11 > y22 or y21 > y12:
        return False
    return p1.touches(p2)
    
def process_poly(rings, tracts, color, count, alpha):
    for points in rings:
            ptlst = list(points)
            if ptlst is None or len(ptlst) < 3:
                print("BAD!")
                continue
            poly = Polygon(ptlst)
            tracts += [poly]
            x,y = poly.exterior.xy
            plt.plot(x,y,color='none',zorder=1)
            patch = PolygonPatch(poly,facecolor=color,edgecolor='none',alpha=alpha,zorder=2)
            ax.add_patch(patch)
            count += 1
    return tracts, count

daShapefile = r"Wards_fall_2014.shape/Wards_Final_Geo_111312_2014_ED.shp"


ax = plt.gca()
ax.spines['top'].set_color('none')
ax.spines['bottom'].set_color('none')
ax.spines['left'].set_color('none')
ax.spines['right'].set_color('none')
ax.set_aspect('equal','datalim')
ax.tick_params(axis='both',labelcolor='none',color='none')

count=0
tracts = []
centers = []

with fiona.open(daShapefile) as shapes:
    #pprint.pprint(shapes[1])
    for feat in shapes:
        geom = feat["geometry"]
        if geom['type'] == "Polygon":
            rings = geom["coordinates"]
            rlist = [rings]
        elif geom['type'] == "MultiPolygon":
            rlist = geom["coordinates"]
        properties = feat['properties']
        dem_vote = properties['CONDEM14']
        rep_vote = properties['CONREP14']
        if dem_vote == 0 and rep_vote == 0:
            color = 'y'
            alph = .5
        else:
            dem_share = dem_vote/(dem_vote+rep_vote)
            if dem_share > .5:
                color = 'blue'
                alph = dem_share
            else :
                color = 'red'
                alph = (1-dem_share)
        for rings in rlist:
            tracts,count = process_poly(rings,tracts,color, count,alph)
        
    print("\nDone!")
        
    
    plt.show()
    print("Drew {0} things.".format(count))

    