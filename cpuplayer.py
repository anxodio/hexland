#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import itertools
from copy import deepcopy
from utils import GAMETYPE

class CpuPlayer():

    EXACT = 0
    LOWERBOUND = -1
    UPPERBOUND = 1

    def __init__(self,cputype,**kwargs):
        self.type = cputype
        self.transtable = {}

    # hg is hexgrid
    def move(self,hg,*largs):

        opt = {
            GAMETYPE["IA_DUMMY"]: self.mvDummy,
            GAMETYPE["IA_EASY"]: self.mvNegamax,
        }

        opt[self.type](hg)
        return True
        

    def mvDummy(self,hg):
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

    def negamax(self,hg,ply,alpha,beta,color,player):
        alphaOrig = alpha

        # Busquem en transp table
        key = str(hg.getState())
        if key in self.transtable:
            ttentry = self.transtable[key]
            if ttentry['ply'] >= ply:
                if ttentry['flag'] == CpuPlayer.EXACT:
                    return ttentry['value'],None,None
                elif ttentry['flag'] == CpuPlayer.LOWERBOUND:
                    alpha = max(alpha,ttentry['value'])
                elif ttentry['flag'] == CpuPlayer.UPPERBOUND:
                    beta = min(beta,ttentry['value'])
                if alpha >= beta:
                    return ttentry['value'],None,None

        if ply == 0:
            score = hg.score()
            return score[player]*color,None,None

        bestValue = float('-infinity')
        bestX = None
        bestY = None
        sz = hg.gridsize
        moves = list(itertools.product(range(0,sz),range(0,sz)))
        random.shuffle(moves)

        for x,y in moves:

            doPass = False
            if x == 0 and y == 0: # Sempre es None, la fem servir com a "passar" per poder-ho integrar al bucle
                doPass = True
            else:
                t = hg.grid[x][y]
                if not t: continue

            state = deepcopy(hg.getState())
            if not doPass:
                if not hg.doMovement(t,player):
                    # Jugada invalida
                    hg.loadState(state)
                    continue
                hg.deleteGroups()

            val = -self.negamax(hg,ply-1,-beta,-alpha,-color,hg.getNextPlayerNum(player))[0]
            hg.loadState(state)

            if bestValue < val:
                bestValue = val
                bestX = x
                bestY = y

            alpha = max(alpha,val)
            if alpha >= beta:
                break # poda

        # Transposition table entry
        ttentry = {'value':bestValue,'ply':ply}
        if bestValue <= alphaOrig:
            ttentry['flag'] = CpuPlayer.EXACT
        elif bestValue >= beta:
            ttentry['flag'] = CpuPlayer.LOWERBOUND
        else:
            ttentry['flag'] = CpuPlayer.UPPERBOUND

        self.transtable[str(hg.getState())] = ttentry

        return bestValue,bestX,bestY

    def mvNegamax(self,hg):
        player = hg.player

        lliures = 0
        sz = hg.gridsize
        for x,y in list(itertools.product(range(0,sz),range(0,sz))):
            t = hg.grid[x][y]
            if t and not t.content:
                lliures += 1

        if lliures > 12:
            ply = 4
        elif lliures > 6:
            ply = 6
        else:
            ply = 8

        bestValue,x,y = self.negamax(hg,ply,float('-infinity'),float('infinity'),1,player)

        if x == 0 and y == 0:
            # Passem
            print "I pass"
            hg.doPass(False)
        else:
            # Juguem
            print "I play at",x,y
            t = hg.grid[x][y]
            hg.manageTurn(t,False)