#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.9.0')

from kivy.uix.widget import Widget
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty,NumericProperty,ListProperty,ObjectProperty
from kivy.atlas import Atlas
from kivy.vector import Vector

from utils import point_inside_polygon
import random

class Tile(Widget):
    grid_x = NumericProperty()
    grid_y = NumericProperty()
    content = NumericProperty()
    group = NumericProperty()
    upperimg = ObjectProperty()

    # Hexagon points: Punts del hexagon en la part superior, pel control de colisions
    p1 = ListProperty([0, 0])
    p2 = ListProperty([0, 0])
    p3 = ListProperty([0, 0])
    p4 = ListProperty([0, 0])
    p5 = ListProperty([0, 0])
    p6 = ListProperty([0, 0])

    def __init__(self,**kwargs):

        self.group = 0 # No te grup
        self.content = kwargs['content']
        self.gridparent = kwargs['caller']
        self.grid_x = kwargs['grid_x']
        self.grid_y = kwargs['grid_y']

        self.upperimg = self.gridparent.baseatlas['tileNone']

        super(Tile, self).__init__(**kwargs)

        # Diferencia amb el centre, segons el que mourem horitzontalment les diferents files
        dif = self.grid_y-int(self.gridparent.gridsize/2)
        offset = 32*dif

        # posicio final, tenint en compte que y=0 està abaix, girem vertricalment
        # perque tingui sentit amb l'array guardada
        self.pos = offset+self.grid_x*65,(self.gridparent.gridsize-self.grid_y-1)*50

    # Metode intern de kivy per detectar touch_up
    def on_touch_up(self, touch):
        # Si no ha sigut drag i fa colisio...
        d = Vector(*touch.pos).distance(touch.opos)
        if d < 10 and self.collide_point(*touch.pos):
            self.gridparent.manageTurn(self)
            return True

    # Sobreescribim funcio
    def collide_point(self, x, y):
        x, y = self.to_local(x, y, True) # relatiu
        return point_inside_polygon(x, y,
                self.p1 + self.p2 + self.p3 + self.p4 + self.p5 + self.p6)

    def getNeighbors(self):
        neighbors_positions = [(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1)] # x,y
        neighbors = []
        for pos in neighbors_positions:
            t = self.gridparent.getTile(self.grid_x+pos[0],self.grid_y+pos[1])
            if t: neighbors.append(t)
        return neighbors



class HexGrid(ScatterLayout):
    gridsize = NumericProperty()
    grid = ListProperty()
    deadGroups = ListProperty()
    baseimg = ObjectProperty()
    player = NumericProperty()

    def __init__(self,**kwargs):
        super(HexGrid, self).__init__(do_rotation=False,scale_min=.5, scale_max=3.)
        self.gridsize = kwargs['gridsize']

        # Preparem atlas d'imatges pels tiles
        self.baseatlas = Atlas('assets/basetiles.atlas')
        self.playeratlas = Atlas('assets/playertiles.atlas')

        # Nomes gridsize inparell
        assert(self.gridsize%2 != 0)

        self.grid = []
        
        self.setup()

    def setup(self):
        # Torn del jugador per defecte
        self.player = 1

        # Posicio i mida segons mida GRID
        self.pos = 10,10
        self.size = self.gridsize*65,89+(int(self.gridsize/2)*(35+65))

        # Com es la illa? Aleatori
        possibleBases = ['tileAutumn','tileGrass','tileSnow','tileMagic','tileLava','tileStone','tileRock']
        self.baseimg = self.baseatlas[random.choice(possibleBases)]

        self.setupGrid()


    def setupGrid(self):
        # Crea i configura el grid
        sz = self.gridsize
        mid = int(sz/2)
        for y in range(0,sz):
            line = []
            dif = abs(mid-y)
            for x in range(0,sz):
                # Comprova si hi ha casella. Les caselles superiors esquerres i inferiors
                # dretes queden buides.
                if y==mid or (y < mid and x >= dif) or (y>mid and x<sz-dif):
                    # Graphics
                    t = Tile(grid_x = x, grid_y = y, caller = self, content = 0)
                    self.add_widget(t)
                    line.append(t)
                else:
                    line.append(None)
            self.grid.append(line)

        self.reloadGridGraphics()

    def getTile(self,x,y):
        # No es poden demanar index negatius
        if x < 0 or y < 0:
            return None
        if x >= self.gridsize or y >= self.gridsize: # Ens demanen un tile inexistent
            return None
        return self.grid[y][x]

    # Agrupa els tiles connectats
    def resetTileGroups(self):
        sz = self.gridsize
        for y in range(0,sz):
            for x in range(0,sz):
                t = self.grid[y][x]
                if t: t.group = 0 # No te grup

    # Assigna tot el grup. També comprova si es un grup mort
    def recursiveSetGroup(self,t,grpnum,dead=True):
        t.group = grpnum
        for nt in t.getNeighbors():
            if nt.content == 0:
                dead = False # el grup té com a minim una llibertat
            elif not nt.group and nt.content == t.content: # No te grup i mateix jugador
                dead = self.recursiveSetGroup(nt,grpnum,dead)
        return dead

    # Agrupa els tiles connectats, aprofita el bucle per comprovar grups morts
    def setTileGroups(self):
        self.resetTileGroups()

        self.deadGroups = []

        lastGroup = 0
        sz = self.gridsize
        for y in range(0,sz):
            for x in range(0,sz):
                t = self.grid[y][x]
                # si es 0 no te sentit agrupar, i no ha de tenir ja grup assignat
                if t and t.content and t.group == 0:
                    # Assignem nou grup
                    lastGroup += 1
                    dead = self.recursiveSetGroup(t,lastGroup)
                    if dead:
                        self.deadGroups.append(lastGroup)

    def deleteGroups(self):
        if self.deadGroups:
            sz = self.gridsize
            for y in range(0,sz):
                for x in range(0,sz):
                    t = self.grid[y][x]
                    if t and t.group in self.deadGroups:
                        t.content = 0 # buidem casella

    # Pinta de costat caselles (jugadors) i grups
    def debugGrid(self):
        txt = ""
        sz = self.gridsize
        for y in range(0,sz):
            for x in range(0,sz):
                t = self.grid[y][x]
                if t:
                    txt += str(t.content)
                else: 
                    txt += " "

            txt += " " # deixem un espai entre mig

            for x in range(0,sz):
                t = self.grid[y][x]
                if t:
                    txt += str(t.group)
                else: 
                    txt += " "
            txt += "\n"
        print txt


    def reloadGridGraphics(self):
        # Actualitza els grafics de cada tile
        sz = self.gridsize
        for y in range(0,sz):
            for x in range(0,sz):
                t = self.grid[x][y]
                if t:
                    if t.content == 0: # No pertany a cap jugador
                        t.upperimg = self.baseatlas['tileNone']
                    elif t.upperimg == self.baseatlas['tileNone']: # Si encara no te imatge...
                        if t.content == 1: # Jugador 1
                            posibles = [i for i in self.playeratlas.textures.keys() if i.startswith("wood")]
                        else: # Jugador 2
                            posibles = [i for i in self.playeratlas.textures.keys() if i.startswith("sand")]

                        t.upperimg = self.playeratlas[random.choice(posibles)]


    def manageTurn(self,t):
        if t.content == 0: # si ja està ocupada res
            t.content = self.player
            self.setTileGroups()
            # Validem que no hi hagi suicidi
            if t.group in self.deadGroups:
                t.content = 0
                print "INVALID MOVE, SUICIDE!" # TODO: Que no sigui un print xD
            else:
                # Correcte, seguim jugada
                self.deleteGroups()
                self.nextPlayer()
                self.reloadGridGraphics()

            self.debugGrid()

    def nextPlayer(self):
        # Gestiona el canvi de jugador
        if self.player == 1: self.player = 2
        elif self.player == 2: self.player = 1




