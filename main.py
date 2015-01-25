import kivy
kivy.require('1.8.0')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.image import Image


class Tile(Image):
    def __init__(self,**kwargs):
        self.grid_x = kwargs['grid_x']
        self.grid_y = kwargs['grid_y']
        self.gridparent = kwargs['caller']
        super(Image, self).__init__(**kwargs)


        self.texture = Image(source="assets/tileSand.png").texture

        # La posicio 0,0 a un scatter (relative) es el centre
        correctx = int(self.gridparent.size[0]/2)-32 # meitat menys mig tile
        correcty = int(self.gridparent.size[1]/2)-44 # meitat menys un tile

        # Diferencia amb el centre, segons el que mourem horitzontalment les diferents files
        dif = self.grid_y-int(self.gridparent.gridsize/2)
        offset = 32*dif

        # posicio final amb les diferents correccions i offsetsint(self.gridsize/2)*35
        self.pos = offset-correctx+self.grid_x*65,correcty-self.grid_y*50

    # TODO: Aqui algo no va bien...
    def on_touch_up(self, touch):
        localtouch = self.to_local(*touch.pos)
        if self.collide_point(*localtouch):
            print self.grid_y,self.grid_x,localtouch
            return True

class HexGrid(ScatterLayout):
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
                    t = Tile(grid_x = x, grid_y = y, caller = self,
                                  content = 's')
                    self.add_widget(t) # tile, zindex
                else:
                    line.append(None)
            self.grid.append(line)


class HexlandGame(Widget):

    def setup(self):
        self.grid = HexGrid(gridsize = 5)
        self.add_widget(self.grid)



class HexlandApp(App):
    def build(self):
    	game = HexlandGame()
    	game.setup()
        return game


if __name__ == '__main__':
    HexlandApp().run()
