#!/usr/bin/env python
# -*- coding: utf-8 -*-

from netease_music_browser import MusicBrowser
from netease_music_playlist import MusicPlaylist
from nls import _
from helper import Dispatcher, SignalCollector
from widget.tab_box import ListTab

music_list = MusicPlaylist()
music_browser = MusicBrowser()
radio_list_tab = ListTab(_("网易云音乐"), music_list, music_browser)

def enable(dmusic):
    Dispatcher.emit("add-source", radio_list_tab)

def disable(dmusic):
    SignalCollector.disconnect_all("neteasecloudmusic")
    Dispatcher.emit("remove-source", radio_list_tab)
