#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.8.0')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty,NumericProperty,ListProperty

# Permet detectar colisio sobre qualsevol poligon
# poly es una llista de parelles (x,y), punts formant el poligon
def point_inside_polygon(x, y, poly):
    '''Source: http://www.ariel.com.au/a/python-point-int-poly.html'''
    n = len(poly)
    inside = False
    p1x = poly[0]
    p1y = poly[1]
    for i in range(0, n + 2, 2):
        p2x = poly[i % n]
        p2y = poly[(i + 1) % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

class Tile(Widget):
    imgsource = StringProperty()
    grid_x = NumericProperty()
    grid_y = NumericProperty()

    # Hexagon points: Punts del hexagon en la part superior, pel control de colisions
    p1 = ListProperty([0, 0])
    p2 = ListProperty([0, 0])
    p3 = ListProperty([0, 0])
    p4 = ListProperty([0, 0])
    p5 = ListProperty([0, 0])
    p6 = ListProperty([0, 0])

    def __init__(self,**kwargs):

        self.imgsource = "assets/tileSand.png"
        self.grid_x = kwargs['grid_x']
        self.grid_y = kwargs['grid_y']
        self.gridparent = kwargs['caller']

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
            self.imgsource = "assets/tileGrass.png"
            return True

    # Sobreescribim funcio
    def collide_point(self, x, y):
        x, y = self.to_local(x, y, True) # relatiu
        return point_inside_polygon(x, y,
                self.p1 + self.p2 + self.p3 + self.p4 + self.p5 + self.p6)

class HexGrid(ScatterLayout):
    gridsize = NumericProperty()
    grid = ListProperty()

    def __init__(self,**kwargs):
        super(HexGrid, self).__init__(do_rotation=False,scale_min=.5, scale_max=3.)
        self.gridsize = kwargs['gridsize']

        # Nomes gridsize inparell
        assert(self.gridsize%2 != 0)
        
        self.grid = []
        self.pos = 10,10
        self.size = self.gridsize*65,89+(int(self.gridsize/2)*(35+65))
        self.setup()

    def setup(self):
        # Crea la capa de sota, de sorra
        sz = self.gridsize
        mid = int(sz/2)
        for y in range(0,sz):
            line = []
            dif = abs(mid-y)
            for x in range(0,sz):
                if y==mid or (y < mid and x >= dif) or (y>mid and x<sz-dif):
                    line.append('s')
                    # Graphics
                    t = Tile(grid_x = x, grid_y = y, caller = self, content = 's')
                    self.add_widget(t) # tile, zindex
                else:
                    line.append(None)
            self.grid.append(line)


class HexlandGame(Widget):

    def setup(self):
        self.grid = HexGrid(gridsize = 11)
        self.add_widget(self.grid)

class HexlandApp(App):
    def build(self):
    	game = HexlandGame()
    	game.setup()
        return game


if __name__ == '__main__':
    HexlandApp().run()
