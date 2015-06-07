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
from kivy.clock import Clock, mainthread
from functools import partial

from cpuplayer import CpuPlayer

from utils import point_inside_polygon
from utils import launchSimpleModal
from utils import GAMETYPE
from utils import playClickSound
import random
import threading

class Tile(Widget):
    grid_x = NumericProperty()
    grid_y = NumericProperty()
    content = NumericProperty()
    group = NumericProperty()
    usedByTerrain = BooleanProperty()
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
        self.usedByTerrain = False # No utilitzat per comptar terreny
        self.content = kwargs['content']
        self.gridparent = kwargs['caller']
        self.grid_x = kwargs['grid_x']
        self.grid_y = kwargs['grid_y']

        self.upperimg = self.gridparent.baseatlas['tileNone']

        super(Tile, self).__init__(**kwargs)

        baseX = self.gridparent.size[0]/2-self.gridparent.drawgridsize[0]/2
        baseY = self.gridparent.size[1]/2-self.gridparent.drawgridsize[1]/2

        # Diferencia amb el centre, segons el que mourem horitzontalment les diferents files
        dif = self.grid_y-int(self.gridparent.gridsize/2)
        offset = 32*dif

        # posicio final, tenint en compte que y=0 està abaix, girem vertricalment
        # perque tingui sentit amb l'array guardada
        self.pos = baseX+offset+self.grid_x*65,baseY+(self.gridparent.gridsize-self.grid_y-1)*50

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
    gametype = NumericProperty()
    grid = ListProperty()
    deadGroups = ListProperty()
    baseimg = ObjectProperty()
    player = NumericProperty()
    lastPass = BooleanProperty(False) # la ultima jugada ha sigut passar?

    def __init__(self,**kwargs):
        super(HexGrid, self).__init__(do_rotation=False,scale_min=.5, scale_max=3.,auto_bring_to_front=False)
        self.gridsize = kwargs['gridsize']
        self.gametype = kwargs['gametype']
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
        self.deads = {1:0,2:0}
        self.resetScore()

        self.setup()

        # Si ens construeixen amb estat, el carreguem
        if kwargs['state']:
            self.loadState(kwargs['state'],True)
            self.reloadGridGraphics()

        # Si estem vs cpu, creem el jugador CPU
        if not self.gametype == GAMETYPE["PVP"]:
            self.cpu = CpuPlayer(self.gametype)


    def setup(self):
        # Torn del jugador per defecte
        self.player = 1

        # Posicio i mida segons mida GRID
        self.drawgridsize = self.gridsize*65,89+(int(self.gridsize/2)*(35+65))

        self.size[0] = 1000
        self.size[1] = 1000

        self.pos = Window.size[0]/2-self.size[0]/2,Window.size[1]/2-self.size[1]/2

        # Com es la illa? Aleatori
        possibleBases = ['tileAutumn','tileGrass','tileSnow','tileMagic','tileLava','tileStone','tileRock']
        self.baseimg = self.baseatlas[random.choice(possibleBases)]

        self.setupGrid()

    def getState(self):
        state = {}
        state["player"] = self.player
        state["gametype"] = int(self.gametype)
        state["deads"] = self.deads
        state["tileScore"] = self.tileScore
        state["terrScore"] = self.terrScore

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

    def loadState(self,state,fromContinue=False):
        grid = state["grid"]
        sz = len(grid)

        # No pot passar que aixo sigui diferent
        assert(sz == self.gridsize)

        for y in range(0,sz):
            for x in range(0,sz):
                t = grid[y][x]
                if t is not None:
                    self.grid[y][x].content = t

        if fromContinue and not state["player"] == self.player: # Nomes 2 jugadors
            self.nextPlayer()

        self.gametype = state["gametype"]
        self.deads = state["deads"]
        self.tileScore = state["tileScore"]
        self.terrScore = state["terrScore"]

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

    # Reseteja les puntuacions actuals
    def resetScore(self):
        self.tileScore = {1:0,2:0}
        self.terrScore = {1:0,2:0}

    # Reseteja els grups dels tiles
    def resetTileGroups(self):
        sz = self.gridsize
        for y in range(0,sz):
            for x in range(0,sz):
                t = self.grid[y][x]
                if t: t.group = 0 # No te grup

    # Reseteja la marca de si el tile ha estat fet servir per puntuar terreny
    def resetTileUsed(self):
        sz = self.gridsize
        for y in range(0,sz):
            for x in range(0,sz):
                t = self.grid[y][x]
                if t: t.usedByTerrain = False

    # Assigna tot el grup. També comprova si es un grup mort
    def recursiveSetGroup(self,t,grpnum,dead=True):
        t.group = grpnum
        for nt in t.getNeighbors():
            if nt.content == 0:
                dead = False # el grup té com a minim una llibertat,
            elif not nt.group and nt.content == t.content: # No te grup i mateix jugador
                dead = self.recursiveSetGroup(nt,grpnum,dead)
        return dead

    # Assigna tot el grup de terreny buit. Torna també informacio per puntuacio de terrany
    def recursiveSetTerrainGroup(self,t,grpnum,terrInfo):
        t.group = grpnum
        terrInfo['count']+=1
        for nt in t.getNeighbors():
            if nt.content and not nt.usedByTerrain: # es un jugador, el sumem i marquem com a fet servit (per a aquest grup)
                nt.usedByTerrain = True
                terrInfo[nt.content]+=1 
            elif not nt.group and nt.content == 0: # No te grup i mateix jugador
                terrInfo = self.recursiveSetTerrainGroup(nt,grpnum,terrInfo)
        return terrInfo

    # Agrupa els tiles connectats, aprofita el bucle per comprovar grups morts i calcular puntuacio
    def setTileGroups(self):
        self.resetTileGroups()
        self.resetScore()

        self.deadGroups = []

        lastGroup = 0
        sz = self.gridsize
        for y in range(0,sz):
            for x in range(0,sz):
                t = self.grid[y][x]
                if t:
                    # Si no es buida, la sumem com a puntuacio de caselles del jugador (tile)
                    if t.content:
                        self.tileScore[t.content]+=1

                    if t.group == 0:
                        # Assignem nou grup
                        lastGroup += 1
                        if t.content:
                            dead = self.recursiveSetGroup(t,lastGroup)
                            if dead:
                                self.deadGroups.append(lastGroup)
                        else:
                            self.resetTileUsed()
                            terrInfo = {'count':0,1:0,2:0}
                            terrInfo = self.recursiveSetTerrainGroup(t,lastGroup,terrInfo)

                            # Puntuacio de terreny
                            if terrInfo[1]>terrInfo[2]:
                                self.terrScore[1]+=terrInfo['count']
                            elif terrInfo[1]<terrInfo[2]:
                                self.terrScore[2]+=terrInfo['count']


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
                    txt += str(t.group) if t.content else str(0) # per no liar, no imprimim els grups de caselles buides
                else: 
                    txt += " "
            txt += "\n"
        print txt
        print self.score()


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


    # Realitza un moviment. Torna fals si no es possible (suicidi), o true en cas contrari
    def doMovement(self,t,player=None):
        if t.content == 0: # si ja està ocupada res
            # Per poder provar jugades desde l'ordinador
            if player: t.content = player
            else: t.content = self.player

            self.setTileGroups()

            # Validem que no hi hagi suicidi
            dead = False
            if t.group in self.deadGroups:
                # Pot ser que sigui un suicidi d'atac: Estas matant un altre grup i per tant no mors
                # Per compvoar això, si hi ha més d'un grup mort, treiem el nostre grup dels grups
                # morts, matem els grups, refem els grups, i si estem vius es jugada valida
                dead = True
                if len(self.deadGroups) > 1:
                    state = self.getState()
                    self.deadGroups.remove(t.group)
                    otherDeads = self.deadGroups

                    self.deleteGroups()
                    self.setTileGroups()
                    if not t.group in self.deadGroups:
                        dead = False

                    self.deadGroups = otherDeads
                    self.loadState(state)

            return not dead
            # if dead:
            #     return False
            # else:
            #     # Correcte, seguim jugada
            #     return True
        else:
            return False

    @mainthread
    def manageTurn(self,t,playerMove=True):
        # Si el jugador intenta jugar mentre es el torn de la IA, no fem res
        if playerMove and not self.gametype == GAMETYPE["PVP"] and self.player == 2:
            return False

        # En cap cas es pot jugar sobre una casella ocupada
        if not t.content == 0:
            return False

        state = self.getState()

        if self.doMovement(t):
            # Correcte, seguim jugada
            self.deleteGroups()
            self.reloadGridGraphics()
            self.lastPass = False

            self.debugGrid()

            # Guardem estat a cada moviment
            self.nextPlayer()
            self.store.put('save',state=self.getState())
        else:
            self.loadState(state)
            launchSimpleModal("INVALID MOVE\nYou can't suicide.")
        playClickSound()


    @mainthread
    def doPass(self,playerMove=True):
        if playerMove and not self.gametype == GAMETYPE["PVP"] and self.player == 2:
            return False

        if not self.gametype == GAMETYPE["PVP"] and self.player == 2:
            launchSimpleModal("CPU passed.")

        if self.lastPass:
            # Final del joc
            self.gameOver()
        else:
            self.lastPass = True
            self.nextPlayer()

    def getNextPlayerNum(self,player):
        if player == 1: player = 2
        elif player == 2: player = 1
        return player

    def nextPlayer(self):
        # Gestiona el canvi de jugador
        self.player = self.getNextPlayerNum(self.player)
        self.gui.setPlayerText(self.player)

        if not self.gametype == GAMETYPE["PVP"] and self.player == 2:
            self.startCpu()

    def startCpu(self):
        threading.Thread(target=self.cpu.move, args=(self,)).start()

    # Retorna la puntuació en un moment concret, desglosada
    def score(self):
        score = {1:0,2:0}
        deadScore = {1:0,2:0}

        # Sumem mortes
        deadScore[1] += self.deads[2] if 2 in self.deads else 0
        deadScore[2] += self.deads[1] if 1 in self.deads else 0

        for k in score.keys():
            score[k]+=deadScore[k]+self.tileScore[k]+self.terrScore[k]

        score['tileScore'] = self.tileScore
        score['terrScore'] = self.terrScore
        score['deadScore'] = deadScore

        return score

    @mainthread
    def gameOver(self):
        score = self.score()

        # Qui ha guanyat?
        whowin = "TIE!"
        if score[1]>score[2]:
            whowin = "Player 1 WINS!"
        elif score[1]<score[2]:
            whowin = "Player 2 WINS!"

        # Esborrem partida, mostrem guanyador, tornem al menu
        if self.store.exists('save'):
            self.store.delete('save')
        launchSimpleModal("Game Finished\nP1: "+str(score[1])+" | P2: "+str(score[2])+"\n"+whowin)
        self.parent.parent.gameOver()


class HexGame(FloatLayout):
    grid = ObjectProperty(None)
    gui = ObjectProperty(None)

    def __init__(self,**kwargs):
        super(HexGame, self).__init__()

        Window.bind(on_keyboard=self.onBackBtn)

        size = Window.size

        self.gui = GameGui()
        self.grid = HexGrid(gridsize=kwargs['gridsize'],gametype=kwargs['gametype'],state=kwargs['state'],gui=self.gui)

        self.add_widget(self.grid)
        self.add_widget(self.gui)

    def onBackBtn(self, window, key, *args):
        """ To be called whenever user presses Back/Esc Key """
        # If user presses Back/Esc Key
        if key == 27:
            self.parent.gameOver()
            return True
        return False

class GameGui(FloatLayout):
    lbl_player = ObjectProperty(None)

    def __init__(self,**kwargs):
        super(GameGui, self).__init__()

    def setPlayerText(self,num):
        self.lbl_player.text = "Player "+str(num)+" turn"

    def passTurn(self):
        self.parent.grid.doPass()
