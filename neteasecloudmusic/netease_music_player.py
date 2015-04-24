#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from config import config

from netease_events import event_manager

try:
    from simplejson import json
except ImportError:
    import json

from xdg_support import get_cache_file

import utils
from netease_api import NetEase

class MusicPlayer(NetEase):
    down_type = link_type = 0
    def __init__(self):
        NetEase.__init__(self)
        self.initial_data()
        self.config_db = get_cache_file("neteasecloudmusic/conf.db")
        self.client_version = "0.01"
        self.is_cloud = 1
        self.mv_songs = None
        self.load()

    def initial_data(self):
        self.logged = self.load_cookie()
        #self.cookie = ""
        #self.username = ""
        self.uid = self.get_uid()

    def save_lyric(self, data, sid):
        save_path = os.path.expanduser(config.get("lyrics", "save_lrc_path"))
        if not os.path.exists(save_path):
            utils.makedirs(save_path)

        try:
            lrc = data['lrc']['lyric']
        except:
            lrc = "[00:00.00] No lyric found\n"
        # deepin music 好像不支持tlyric, tlyric应该是英文歌词的翻译
        # 最好能把英文和翻译合并起来
        #try:
            #tlyric = data['tlyric']['lyric']
        #except:
            #tlyric = None
        #try:
            #klyric = data['klyric']['lyric']
        #except:
            #klyric = None
        #lrc_content = klyric or lrc or tlyric
        lrc_content = lrc
        lrc_path = os.path.join(save_path, str(sid)+'.lrc')
        if not os.path.exists(lrc_path) and lrc_content:
            with open(lrc_path, 'w') as f:
                f.write(str(lrc_content))

        return lrc_path

    @property
    def ClientInfo(self):
        info = dict(cookie=self.cookie,
                client_version = self.client_version)
        return json.dumps(info)

    def Playlists(self):
        return {item['id']:item['name'] for item in
                NetEase().user_playlist(self.uid, offset=0)}

    def AddSongs(self, dummy_songs):
        songs = self.parse_dummy_songs(dummy_songs)
        if songs:
            event_manager.emit("add-songs", songs)

    def PlaySongs(self, dummy_songs):
        songs = self.parse_dummy_songs(dummy_songs)
        if songs:
            event_manager.emit("play-songs", songs)

    def FavoriteSongs(self, dummy_songs):
        songs = self.parse_dummy_songs(dummy_songs)
        if songs:
            event_manager.emit("collect-songs", songs)

    @classmethod
    def parse_dummy_songs(cls, dummy_songs, stringify=True):
        if stringify:
            dummy_songs = json.loads(
                    cls.js_context.JSON.stringify(dummy_songs))

        songs = []
        for s in dummy_songs:
            song = parse_to_dsong(s)
            if song:
                songs.append(song)

        return songs

    @property
    def is_login(self):
        if not self.logged:
            self.logged = self.load_cookie()
        return self.logged

    def relogin(self):
        self.save_cookie(None)
        self.initial_data()
        self.logged = False

    def alert(self, *args):
        print args

    def PhoenixLogin(self, login_type, act):
        print "login_type: ", login_type, act

    def SetLoginStatus(self, cookie, username, uid):
        print "login_type"
        self.cookie = cookie
        self.username = username
        self.uid = uid
        if self.cookie:
            event_manager.emit("login-success")
        self.save()

    def load(self):
        obj = utils.load_db(self.config_db)
        if obj:
            for key, value, in obj.items():
                setattr(self, key, value)

    def save(self):
        obj = dict(cookie=self.cookie,
                username=self.username,
                uid=self.uid)
        utils.save_db(obj, self.config_db)

class PlayerInterface(object):

    def setLoginCallBackType(self, down_type):
        MusicPlayer.down_type = down_type

neteasecloud_music_player = MusicPlayer()
player_interface = PlayerInterface()
