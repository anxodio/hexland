#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import itertools

class CpuPlayer():

    def __init__(self,cputype,**kwargs):
        self.type = cputype

    # hg is hexgrid
    def move(self,hg):

        sz = hg.gridsize
        possibles = list(itertools.product(range(0,sz),range(0,sz)))

        finished = False
        while not finished:
            if not len(possibles): break # sortim i passem
            
            x,y = random.choice(possibles)
            t = hg.grid[x][y]
            if t and t.content == 0:
                state = hg.getState()
                if hg.doMovement(t):
                    finished = True
                hg.loadState(state)

            if not finished:
                possibles.remove((x,y))
        else:
            # Trobat, juguem
            hg.manageTurn(t,False)
            return

        # No trobat, passem
        hg.doPass(False)