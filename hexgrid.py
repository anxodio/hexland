#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.8.0')

from kivy.uix.widget import Widget
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty,NumericProperty,ListProperty,ObjectProperty
from kivy.atlas import Atlas

from utils import point_inside_polygon
import random

class Tile(Widget):
    grid_x = NumericProperty()
    grid_y = NumericProperty()
    content = NumericProperty()
    upperimg = ObjectProperty()

    # Hexagon points: Punts del hexagon en la part superior, pel control de colisions
    p1 = ListProperty([0, 0])
    p2 = ListProperty([0, 0])
    p3 = ListProperty([0, 0])
    p4 = ListProperty([0, 0])
    p5 = ListProperty([0, 0])
    p6 = ListProperty([0, 0])

    def __init__(self,**kwargs):

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

    def on_touch_up(self, touch):
        # Si no ha sigut drag i fa colisio...
        if touch.pos == touch.opos and self.collide_point(*touch.pos):
            self.gridparent.manageTurn(self)
            return True

    # Sobreescribim funcio
    def collide_point(self, x, y):
        x, y = self.to_local(x, y, True) # relatiu
        return point_inside_polygon(x, y,
                self.p1 + self.p2 + self.p3 + self.p4 + self.p5 + self.p6)

class HexGrid(ScatterLayout):
    gridsize = NumericProperty()
    grid = ListProperty()
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
            self.reloadGridGraphics()
            self.nextPlayer()

    def nextPlayer(self):
        # Gestiona el canvi de jugador
        if self.player == 1: self.player = 2
        elif self.player == 2: self.player = 1




