#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.0.1"

import kivy
kivy.require('1.9.0')

from kivy.app import App
from kivy.uix.widget import Widget

from hexgrid import HexGrid

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
