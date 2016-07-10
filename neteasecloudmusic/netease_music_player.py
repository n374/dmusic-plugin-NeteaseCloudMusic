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
from song import Song as deepin_Song

import utils
from player import Player
from netease_api import NetEase

try:
    from encrypted import encrypted_id
    print "found encrypted.py"
except:
    pass

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

    def save_lyric(self, data, sid, name, artist):
        save_path = os.path.expanduser(config.get("lyrics", "save_lrc_path"))
        if not os.path.exists(save_path):
            utils.makedirs(save_path)

        try:
            lrc = data['lrc']['lyric']
        except:
            lrc = "[00:00.00] "+name+' - '+artist+"\n[99:59:99] No lyric found\n"
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

    def get_better_quality_music(self, song):
        try:
            # 在有加密算法的情况下优先获取320K url
            song_dfsId = str(song['hMusic']['dfsId'])
            encrypted_song_id = encrypted_id(song_dfsId)
            song['uri'] = 'http://m1.music.126.net/' + encrypted_song_id + '/' + song_dfsId + '.mp3'
        except:
            try:
                # 在有加密算法的情况下获取160K url
                song_dfsId = str(song['mMusic']['dfsId'])
                encrypted_song_id = encrypted_id(song_dfsId)
                song['uri'] = 'http://m1.music.126.net/' + encrypted_song_id + '/' + song_dfsId + '.mp3'
            except:
                song['uri'] = song['mp3Url']
        return song

    @property
    def ClientInfo(self):
        info = dict(cookie=self.cookie,
                client_version = self.client_version)
        return json.dumps(info)

    def Playlists(self):
        return {item['id']:item['name'] for item in
                NetEase().get_user_playlist(self.uid, offset=0)}

    def AddSongs(self, songs):
        if songs:
            event_manager.emit("add-songs", songs)

    def handle_songs_info(self, songs):
        save_path = os.path.expanduser(config.get("lyrics", "save_lrc_path"))
        handled_songs = []
        for song in songs:
            url = self.get_songs_url([song.song_id])[0]['url']
            if not url:
                self.get_next_song()
                return
            # Conver to deepin_Song so deepin music player can get info
            self.save_lyric(self.get_lyric(song.song_id), song.song_id,
                    song.song_name, song.artist_names)
            song_dict = {}
            song_dict['sid'] = song.song_id
            song_dict['artist'] = song.artist_names
            song_dict['location_lrc'] = os.path.join(save_path, str(song.song_id)+'.lrc')
            song_dict['uri'] = url
            song_dict['title'] = song.song_name
            song_dict['album'] = song.album_name
            song_dict['album_cover_url'] = song.album_pic
            song_dict['#duration'] = song.duration
            song_dict['song_type'] = 'unknown'
            handled_songs.append(deepin_Song(song_dict))
        return handled_songs

    def play_song(self, song, play=False):
        if not song:
            return None

        Player.play_new(self.handle_songs_info([song])[0])

        event_manager.emit("save")

    def PlaySongs(self, songs):
        if songs:
            event_manager.emit("play-songs", songs)

    def FavoriteSongs(self, songs):
        if songs:
            event_manager.emit("collect-songs", songs)

    @property
    def is_login(self):
        if not self.logged:
            self.logged = self.load_cookie()
        return self.logged

    def relogin(self):
        self.save_cookie(None)
        self.cookies = None
        self.initial_data()
        self.logged = False

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
