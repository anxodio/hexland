#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.9.0')

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.atlas import Atlas
from kivy.properties import ObjectProperty
from kivy.animation import Animation
from kivy.storage.dictstore import DictStore

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

    def continueDisabled(self):
        return not self.store.exists('save')



class NewMenu(Widget):

    opt_5 = ObjectProperty(None)
    opt_7 = ObjectProperty(None)
    opt_9 = ObjectProperty(None)

    opt_ia = ObjectProperty(None)
    opt_pvp = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(NewMenu, self).__init__(**kwargs)

    def start(self):
        # Busquem els valors escollits
        size = 5
        if self.opt_7.state == "down":
            size = 7
        elif self.opt_9.state == "down":
            size = 9

        vs = GAMETYPE["PVP"]
        if self.opt_ia.state == "down":
            vs = GAMETYPE["IA_EASY"]

        self.parent.start(size,vs)