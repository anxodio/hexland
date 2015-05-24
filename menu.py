#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.9.0')

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.atlas import Atlas
from kivy.properties import ObjectProperty, StringProperty
from kivy.animation import Animation
from kivy.storage.dictstore import DictStore
from kivy.core.window import Window

from utils import GAMETYPE

class Menu(Widget):

    logo_img = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.uiatlas = Atlas('assets/uitiles.atlas')
        self.store = DictStore('hexland.dict')
        super(Menu, self).__init__(**kwargs)


        self.logo_img.size_hint = 0.1,0.1

        Animation(size_hint=(0.8,0.3),t='out_bounce').start(self.logo_img)

    def new(self):
        self.parent.setup()

    def load(self):
        state = self.store.get('save')['state']
        size = len(state['grid'])
        vs = state['gametype']
        self.parent.start(size,vs,state)

    def help(self):
        self.parent.help()

    def continueDisabled(self):
        return not self.store.exists('save')



class NewMenu(Widget):

    opt_5 = ObjectProperty(None)
    opt_7 = ObjectProperty(None)
    opt_9 = ObjectProperty(None)

    opt_iadummy = ObjectProperty(None)
    opt_iaeasy = ObjectProperty(None)
    opt_pvp = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(NewMenu, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.onBackBtn)

    def start(self):
        # Busquem els valors escollits
        size = 5
        if self.opt_7.state == "down":
            size = 7
        elif self.opt_9.state == "down":
            size = 9

        vs = GAMETYPE["PVP"]
        if self.opt_iadummy.state == "down":
            vs = GAMETYPE["IA_DUMMY"]
        elif self.opt_iaeasy.state == "down":
            vs = GAMETYPE["IA_EASY"]

        self.parent.start(size,vs)

    def onBackBtn(self, window, key, *args):
        """ To be called whenever user presses Back/Esc Key """
        # If user presses Back/Esc Key
        if key == 27:
            self.parent.gameOver()
            return True
        return False

class Help(Widget):

    helpText = StringProperty("")

    def __init__(self, **kwargs):
        super(Help, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.onBackBtn)

        self.helpText = """
Welcome to Hexland!
*******************

Hexland is a game based in Go, and ancient oriental table game. If know how to play Go, you can play Hexland without any problem.

The objective is conquer the island, getting more terrain than your adversary. In every turn you put a single building in the island. If your buildings surround the other player buildings, their buildings are destroyed.
You can't suicide (put a building in a sorrounded position), unless you sorround your adversary at same time. So try to keep always at least two eyes in your formations to protect them of being surrounded.

Game finishes when the two players pass turn in a row, and the player with more buildings, surrounded terrain and kills wins the game.
        """

    def onBackBtn(self, window, key, *args):
        """ To be called whenever user presses Back/Esc Key """
        # If user presses Back/Esc Key
        if key == 27:
            self.parent.gameOver()
            return True
        return False