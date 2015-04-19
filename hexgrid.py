#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.9.0')

from kivy.uix.widget import Widget
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty,NumericProperty,ListProperty,ObjectProperty,BooleanProperty,DictProperty
from kivy.atlas import Atlas
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.storage.dictstore import DictStore

from utils import point_inside_polygon
from utils import launchSimpleModal
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

    def on_touch_down(self, touch):
        touch.grab(self) # Preparo el touch (l'agafo)

    # Metode intern de kivy per detectar touch_up
    def on_touch_up(self, touch):
        # Perque sigui valid, ha de començar en aquesta mateixa classe (drag),
        # no ser drag (distancia) i no ser un press molt llarg (time)
        time = touch.time_end-touch.time_start
        d = Vector(*touch.pos).distance(touch.opos)
        if touch.grab_current is self and d < 10 and time < 0.5 and self.collide_point(*touch.pos):
            touch.ungrab(self)
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
    lastPass = BooleanProperty(False) # la ultima jugada ha sigut passar?

    def __init__(self,**kwargs):
        super(HexGrid, self).__init__(do_rotation=False,scale_min=.5, scale_max=3.,auto_bring_to_front=False)
        self.gridsize = kwargs['gridsize']
        self.gui = kwargs['gui']

        # Preparem atlas d'imatges pels tiles
        self.baseatlas = Atlas('assets/basetiles.atlas')
        self.playeratlas = Atlas('assets/playertiles.atlas')
        self.uiatlas = Atlas('assets/uitiles.atlas')

        # Nomes gridsize inparell
        assert(self.gridsize%2 != 0)

        # Preparem store
        self.store = DictStore('hexland.dict')

        self.grid = []
        self.deads = {}

        self.setup()

        # Si ens construeixen amb estat, el carreguem
        if kwargs['state']:
            self.loadState(kwargs['state'])
            self.reloadGridGraphics()

    def setup(self):
        # Torn del jugador per defecte
        self.player = 1

        # Posicio i mida segons mida GRID
        self.size = self.gridsize*65,89+(int(self.gridsize/2)*(35+65))
        self.pos = Window.size[0]/2-self.size[0]/2,Window.size[1]/2-self.size[1]/2

        # Com es la illa? Aleatori
        possibleBases = ['tileAutumn','tileGrass','tileSnow','tileMagic','tileLava','tileStone','tileRock']
        self.baseimg = self.baseatlas[random.choice(possibleBases)]

        self.setupGrid()

    def getState(self):
        state = {}
        state["player"] = self.player
        state["deads"] = self.deads

        grid = []
        sz = self.gridsize
        for y in range(0,sz):
            row = []
            for x in range(0,sz):
                t = self.grid[y][x]
                if t:
                    row.append(t.content)
                else:
                    row.append(None)
            grid.append(row)
        state["grid"] = grid
        return state

    def loadState(self,state):
        grid = state["grid"]
        sz = len(grid)

        # No pot passar que aixo sigui diferent
        assert(sz == self.gridsize)

        for y in range(0,sz):
            for x in range(0,sz):
                t = grid[y][x]
                if t is not None:
                    self.grid[y][x].content = t

        if not state["player"] == self.player: # Nomes 2 jugadors
            self.nextPlayer()

        self.deads = state["deads"]


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
                        # Contem la mort
                        pl = t.content
                        if pl in self.deads:
                            self.deads[pl]+=1
                        else:
                            self.deads[pl]=1

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
        print self.deads


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
            # Guardem estat actual (per si hem de cancelar la jugada)
            state = self.getState()
            t.content = self.player

            self.setTileGroups()

            # Validem que no hi hagi suicidi
            dead = False
            if t.group in self.deadGroups:
                # Pot ser que sigui un suicidi d'atac: Estas matant un altre grup i per tant no mors
                # Per compvoar això, si hi ha més d'un grup mort, treiem el nostre grup dels grups
                # morts, matem els grups, refem els grups, i si estem vius es jugada valida
                dead = True
                if len(self.deadGroups) > 1:
                    self.deadGroups.remove(t.group)
                    self.deleteGroups()
                    self.setTileGroups()
                    if not t.group in self.deadGroups:
                        dead = False

            if dead:
                self.loadState(state)
                launchSimpleModal("INVALID MOVE\nYou can't suicide.")
            else:
                # Correcte, seguim jugada
                self.deleteGroups()
                self.nextPlayer()
                self.reloadGridGraphics()
                self.lastPass = False

                # Guardem estat a cada moviment
                self.store.put('save',state=self.getState())

            self.debugGrid()

    def doPass(self):
        if self.lastPass:
            # Final del joc
            self.gameOver()            
        else:
            self.nextPlayer()
            self.lastPass = True

    def nextPlayer(self):
        # Gestiona el canvi de jugador
        if self.player == 1: self.player = 2
        elif self.player == 2: self.player = 1
        self.gui.setPlayerText(self.player)

    def gameOver(self):
        # Mirem qui ha guanyat
        score = {1:0,2:0}

        # Primer caselles al mapa
        sz = self.gridsize
        for y in range(0,sz):
            for x in range(0,sz):
                t = self.grid[x][y]
                if t and t.content:
                    score[t.content]+=1

        # Sumem mortes
        score[1] += self.deads[2] if 2 in self.deads else 0
        score[2] += self.deads[1] if 1 in self.deads else 0

        # Qui ha guanyat?
        whowin = "1"
        if score[2]>score[1]:
            whowin = "2"

        # Esborrem partida, mostrem guanyador, tornem al menu
        if self.store.exists('save'):
            self.store.delete('save')
        launchSimpleModal("Game Finished\nPlayer "+whowin+" WINS!")
        self.parent.parent.gameOver()


class HexGame(FloatLayout):
    grid = ObjectProperty(None)
    gui = ObjectProperty(None)

    def __init__(self,**kwargs):
        super(HexGame, self).__init__()
        size = Window.size

        self.gui = GameGui()
        self.grid = HexGrid(gridsize=kwargs['gridsize'],state=kwargs['state'],gui=self.gui)

        self.add_widget(self.grid)
        self.add_widget(self.gui)

class GameGui(FloatLayout):
    lbl_player = ObjectProperty(None)

    def __init__(self,**kwargs):
        super(GameGui, self).__init__()

    def setPlayerText(self,num):
        self.lbl_player.text = "Player "+str(num)+" turn"

    def passTurn(self):
        self.parent.grid.doPass()
