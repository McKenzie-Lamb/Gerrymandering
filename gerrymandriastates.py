# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 14:18:35 2017

@author: wr
"""

from shapely.geometry import Polygon
from shapely.geometry import Point
from shapely.ops import cascaded_union
from descartes.patch import PolygonPatch
import random

def is_adjacent(shape1, shape2):
        return (shape1 is not shape2 and shape1.touches(shape2) 
                 and not isinstance(shape1.intersection(shape2),Point))

class CBlock:
    def __init__(self, dems, reps, population, shape):
        self.dems = dems 
        self.reps = reps 
        self.population = population
        self.shape = shape
        self.state = None
        self.district = None
        
    def __str__(self):
        return "({0}-{1})".format(self.dems,self.reps)
        
    def plot_block(self, plot):
        dem_share = self.dems/(self.dems+self.reps)
        if dem_share > .5:
            color = 'blue'
            alph = dem_share
        elif dem_share < .5:
            color = 'red'
            alph = (1-dem_share)
        else:
            color = 'magenta'
            alph = 1
        x,y = self.shape.exterior.xy
        plot.plot(x,y,color='none',zorder=1)
        patch = PolygonPatch(self.shape,facecolor=color,edgecolor='none',alpha=alph,zorder=2)
        plot.add_patch(patch)
        
    def is_adjacent(self, other_block):
        return is_adjacent(self.shape,other_block.shape)

class District:
    def __init__(self, name, cblocks, dems, reps, winner):
        self.name = name
        self.cblocks = cblocks
        self.shape = cascaded_union([cblock.shape for cblock in cblocks])
        self.dems = dems
        self.reps = reps
        self.population = sum([block.population for block in cblocks])
        self.winner = winner
        for cblock in cblocks:
            cblock.district = self
        self.index = None
        
    def __str__(self):
        return self.name
        
    def plot_district(self,plot):
        for block in self.cblocks:
            block.plot_block(plot)
        x,y=self.shape.exterior.xy
        plot.plot(x,y,linestyle='dotted',color='black',lw=2)
        c = self.shape.centroid.coords[0]
        plot.text(c[0],c[1],self)

class State:
    def __init__(self, name, districts, all_cblocks):
        self.name = name 
        self.districts = districts
        self.shape = cascaded_union([district.shape for district in districts])
        self.all_cblocks = all_cblocks
        for cblocks in all_cblocks:
            for cblock in cblocks:
                cblock.state = self
        self.adjacent_blocks = []
        index = 0
        for district in districts:
            row = []
            district.index = index
            for other_district in districts:
                adj = self.find_adjacent(district,other_district)[0]
                row.append(adj)
            self.adjacent_blocks.append(row)
            index += 1
            
        
    def __str__(self):
        return self.name
        
    def plot_state(self,plot):
        for district in self.districts:
            district.plot_district(plot)
        x,y = self.shape.exterior.xy
        plot.plot(x,y,color='black',lw=3)
        
    def find_adjacent(self, district1, district2):
        adj_from = set()
        adj_to = set()
        if district1 is not district2:                    
            for block in district1.cblocks:
                for other_block in district2.cblocks:
                    if block.is_adjacent(other_block):
                        adj_from.add(block)
                        adj_to.add(other_block)
        return adj_from,adj_to

    def pairwise_swap(self,district1, district2):
        if (district1 is district2 or not is_adjacent(district1.shape,district2.shape)
            or district1.state is not self or district2.state is not self):
                return False
        #choose a random block in district1 which is adjacent to district2 and vice versa
        adj_blocks1 = self.adjacent_blocks[district1.index][district2.index]
        adj_blocks2 = self.adjacent_blocks[district2.index][district1.index]
        adj1 = random.choice(adj_blocks1)
        adj2 = random.choice(adj_blocks2)
        #make new local districts swapping the blocks
        new_d1 = district1.cblocks.copy()
        new_d2 = district2.cblocks.copy()
        new_d1.remove(adj1)
        new_d1.add(adj2)
        new_d2.remove(adj2)
        new_d2.add(adj1)
        #if the new districts are not contiguous, bail out
        shape1 = cascaded_union([b.shape for b in new_d1])
        shape2 = cascaded_union([b.shape for b in new_d2])
        if(not (isinstance(shape1,Polygon) and isinstance(shape2,Polygon))):
            return False
        #modify the districts to reflect the swapped blocks.
        district1.cblocks = new_d1
        district2.cblocks = new_d2
        district1.shape = shape1
        district2.shape = shape2
        adj_blocks1,adj_blocks2 = self.find_adjacent(district1,district2)
        self.adjacent_blocks[district1.index][district2.index] = adj_blocks1
        self.adjacent_blocks[district2.index][district1.index] = adj_blocks2
        return True

def draw_state_grid(states, width, plot):
    height = len(states)//width
    i = 0
    j = 0
    import matplotlib.gridspec as gridspec
    gs = gridspec.GridSpec(width, height)
    gs.update(wspace=0,hspace=0)
    #plt.gca().set_aspect('equal','datalim')
    for state in states:
        ax = plot.subplot(gs[i,j])
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_color('none')
        ax.spines['right'].set_color('none')
        #ax.set_aspect('equal','datalim')
        ax.tick_params(axis='both',labelcolor='none',color='none')

        state.plot_state(ax)
        i = (i+1) % width
        if i == 0:
            j += 1
