import kivy
kivy.require('1.8.0')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.image import Image

class Tile(Image):
    def __init__(self,**kwargs):
        self.rev_x = kwargs['rev_x']
        self.rev_y = kwargs['rev_y']
        self.gridparent = kwargs['rev_caller']
        super(Image, self).__init__(**kwargs)


        self.texture = Image(source="assets/tileSand.png").texture

        dif = self.rev_y-int(self.gridparent.gridsize)
        offset = 32*dif


        self.pos = offset+self.rev_x*65,self.rev_y*51

class HexGrid(ScatterLayout):
    def __init__(self,**kwargs):
        super(HexGrid, self).__init__(do_rotation=False,scale_min=.5, scale_max=3.)
        self.gridsize = kwargs['gridsize']

        # Nomes gridsize inparell
        assert(self.gridsize%2 != 0)
        
        self.grid = []
        self.pos = 10,10
        self.size = 455,461
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
                    t = Tile(rev_x = x, rev_y = y, rev_caller = self,
                                  rev_content = 's')
                    self.add_widget(t,500+y) # tile, zindex
                else:
                    line.append(None)
            self.grid.append(line)


class HexlandGame(Widget):

    def setup(self):
        self.grid = HexGrid(gridsize = 7)
        self.add_widget(self.grid)



class HexlandApp(App):
    def build(self):
    	game = HexlandGame()
    	game.setup()
        return game


if __name__ == '__main__':
    HexlandApp().run()
