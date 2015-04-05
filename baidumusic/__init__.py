#! /usr/bin/env python
# -*- coding: utf-8 -*-

from music_browser import MusicBrowser
from music_playlist import MusicPlaylist
from nls import _
from helper import Dispatcher, SignalCollector
from widget.tab_box import  ListTab

music_browser = MusicBrowser()
music_list = MusicPlaylist()
radio_list_tab = ListTab(_("百度音乐"), music_list, music_browser)

def enable(dmusic):
    Dispatcher.emit("add-source", radio_list_tab)
    
def disable(dmusic):    
    SignalCollector.disconnect_all("baidumusic")
    Dispatcher.emit("remove-source", radio_list_tab)
