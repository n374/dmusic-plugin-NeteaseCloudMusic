#! /usr/bin/env python
# -*- coding: utf-8 -*-

from events import event_manager

try:
    from simplejson import json
except ImportError:    
    import json
    
from resources import parse_to_dsong, BaseInterface
from xdg_support import get_cache_file
# from helper import Dispatcher

import utils

class jsobject_to_python(object):
    
    def __init__(self, func):
        self.func = func
        
    def __get__(self, obj, cls):    
        def wrapper(jsobject):
            pyobject = json.loads(obj.js_context.JSON.stringify(jsobject))
            return self.func(obj, pyobject)
        return wrapper
    
class jsobject_to_json(object):
    
    def __init__(self, func):
        self.func = func
        
    def __get__(self, obj, cls):    
        def wrapper(jsobject):
            jsonobj = obj.js_context.JSON.stringify(jsobject)
            return self.func(obj, jsonobj)
        return wrapper

class MusicPlayer(BaseInterface):        
    
    down_type = link_type = 0
    
    def __init__(self):
                        
        self.initial_data()
        self.config_db = get_cache_file("baidumusic/conf.db")
        self.client_version = "8.2.0.9"
        self.is_cloud = 1
        self.mv_songs = None
        self.load()
        
    def initial_data(self):    
        self.bduss = ""
        self.username = ""
        self.uid = ""
        self.flag = 1
        self.level = 1
        self.is_hq_enabled = 0
            
    @property
    def ClientInfo(self):
        info = dict(bduss=self.bduss,
                    client_version=self.client_version,
                    is_hq_enabled=self.is_hq_enabled,
                    vip_level=self.level,
                    )
        return json.dumps(info)
    
    def AddSongs(self, dummy_songs):
        ''' '''
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
            
    def GetSongInfos(self):          
        return self.mv_songs
        
    @jsobject_to_json
    def PlayMVs(self, e):
        self.mv_songs = e
        # event_manager.emit("play-mv")
    
    @jsobject_to_python
    def PlayRadios(self, e):    
        print e
    
    @jsobject_to_python
    def DownloadSongs(self, args):    
        print args
        
    @classmethod    
    def parse_dummy_songs(cls, dummy_songs, stringify=True):    
        if stringify:
            dummy_songs = json.loads(cls.js_context.JSON.stringify(dummy_songs))
        
        songs = []
        for s in dummy_songs:
            song = parse_to_dsong(s)
            if song:
                songs.append(song)
        return songs        
     
    @property
    def is_login(self):
        return bool(self.bduss)
    
    def Login(self):
        event_manager.emit("login-dialog-run")
        
    def relogin(self):    
        self.initial_data()
        self.Login() 
        
    def alert(self, *args):    
        print args
        
    def PhoenixLogin(self, login_type, act):
        print "login_type: ", login_type, act
        
    def SetLoginStatus(self, bduss, username, uid, flag, level):    
        print "login_type"
        self.bduss = bduss
        self.username = username
        self.uid = uid
        self.flag = flag
        self.level = level
        if self.bduss:
            event_manager.emit("login-success")
        self.save()    
        
    @jsobject_to_python
    def SetLoginStatus2(self, infos):    
        self.bduss = infos.get("bduss", "")
        self.uid = str(infos.get("user_id", ""))
        self.username = infos.get("user_name", "")
        self.flag = infos.get("auto_login", 1)
        self.level = infos.get("vip_level", 0)
        if self.bduss:
            event_manager.emit("login-success")
        self.save()    
        
            
    def load(self):        
        obj = utils.load_db(self.config_db)
        if obj:
            for key, value, in obj.items():
                setattr(self, key, value)
    
    def save(self):
        obj = dict(bduss=self.bduss,
                   username=self.username,
                   uid=self.uid,
                   flag=self.flag,
                   level=self.level)
        utils.save_db(obj, self.config_db)
                
class PlayerInterface(object):
    
    def setLoginCallBackType(self, down_type):
        MusicPlayer.down_type = down_type
        
        
class TTPDownload(object):        
    
    def init(self, down_type, dummy_songs):
        print "Don't support"
        # songs = MusicPlayer.parse_dummy_songs(dummy_songs)
        # Dispatcher.emit("download-songs", songs)

baidu_music_player = MusicPlayer()        
player_interface = PlayerInterface()
ttp_download = TTPDownload()
