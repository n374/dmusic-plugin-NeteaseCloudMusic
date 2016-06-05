#!/usr/bin/env python
# -*- coding: utf-8 -*-

from netease_music_browser import MusicBrowser
from netease_left_pannel import LeftPannel
from nls import _
from helper import Dispatcher, SignalCollector
from widget.tab_box import ListTab

left_pannel = LeftPannel()
music_browser = MusicBrowser()
radio_list_tab = ListTab(_("网易云音乐"), left_pannel, music_browser)

def enable(dmusic):
    Dispatcher.emit("add-source", radio_list_tab)

def disable(dmusic):
    SignalCollector.disconnect_all("neteasecloudmusic")
    Dispatcher.emit("remove-source", radio_list_tab)
