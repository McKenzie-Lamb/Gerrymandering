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
import copy

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
        self.the_state = None
        
    def __str__(self):
        return self.name
        
    def clone(self):
        return District(self.name,copy.copy(self.cblocks),self.dems,self.reps,self.winner)
        
        
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

        for district in districts:
            district.the_state = self
            
        
    def __str__(self):
        return self.name
        
    def __eq__(self,other):
        return isinstance(other,State) and self.name == other.name
        
    def __hash__(self):
        return self.name.__hash__()
        
    def clone(self):
        return State(self.name,self.districts,self.all_cblocks)
        
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
        """Returns a new state with a swap of adjacent blocks if possible.
        If not, returns False"""
        
  #      print("Comparing",district1,"and",district2)
        if (district1 is district2 or not is_adjacent(district1.shape,district2.shape)):
#            or district1.the_state is not self or district2.the_state is not self):
                return False
        #other = self.clone()
        #choose a random block in district1 which is adjacent to district2 and vice versa
#        adj_blocks1 = self.adjacent_blocks[district1.index][district2.index]
#        adj_blocks2 = self.adjacent_blocks[district2.index][district1.index]
        adj_blocks1,adj_blocks2 = self.find_adjacent(district1,district2)
        #adj1 = random.choice(list(adj_blocks1))
        #adj2 = random.choice(list(adj_blocks2))
        adj1 = adj_blocks1.pop()
        adj2 = adj_blocks2.pop()
        #print(adj_blocks1,":",adj1)
        
        #make new local districts swapping the blocks
        district1.cblocks.remove(adj1)
        district1.cblocks.add(adj2)
        district2.cblocks.remove(adj2)
        district2.cblocks.add(adj1)
        #if the new districts are not contiguous, bail out
        shape1 = cascaded_union([b.shape for b in district1.cblocks])
        shape2 = cascaded_union([b.shape for b in district2.cblocks])
        if(not (isinstance(shape1,Polygon) and isinstance(shape2,Polygon))):
            district1.cblocks.remove(adj2)
            district1.cblocks.add(adj1)
            district2.cblocks.remove(adj1)
            district2.cblocks.add(adj2)
            return False
        #modify the districts to reflect the swapped blocks.
        district1.shape = shape1
        district2.shape = shape2
        return self
        
    def random_district(self,exceptions=None):
        if exceptions is None: 
            exceptions = {}
        district = random.choice(list(self.districts))
        while district in exceptions:
            district = random.choice(list(self.districts))
        return district
        
        

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
