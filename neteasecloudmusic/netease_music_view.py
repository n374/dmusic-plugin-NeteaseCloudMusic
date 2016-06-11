#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gobject
import copy
import time
import random
import os

from dtk.ui.treeview import TreeView
from dtk.ui.threads import post_gui
from dtk.ui.menu import Menu
from HTMLParser import HTMLParser

from widget.ui_utils import render_item_text, draw_single_mask, draw_alpha_mask
from player import Player

import utils
import pango
from xdg_support import get_cache_file
from nls import _
from config import config
from dtk.ui.treeview import TreeItem
from dtk.ui.utils import get_content_size
from dtk.ui.constant import ALIGN_START

from netease_music_player import neteasecloud_music_player as nplayer
from netease_events import event_manager
from netease_music_song import Song
from netease_music_song_item import SongItem

class MusicView(TreeView):
    # 播放列表
    PLAYING_LIST_TYPE = 1
    # 我喜欢的音乐
    FAVORITE_LIST_TYPE = 2
    # 创建的歌单
    CREATED_LIST_TYPE = 3
    # 收藏的歌单
    COLLECTED_LIST_TYPE = 4
    # 登录窗口
    LOGIN_LIST_TYPE = 5
    # 私人FM
    PERSONAL_FM_ITEM = 6

    # 列表循环
    LIST_REPEAT = 1
    # 单曲循环
    SINGLE_REPEAT = 2
    # 顺序播放
    ORDER_PLAY = 3
    # 随机播放
    RANDOMIZE = 4

    FAVORITE_SONGS = []
    CREATED_LISTS_DICT = {}

    online_thread_id = 0

    __gsignals__ = {
            "begin-add-items" :
                (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            "empty-items" :
                (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
            }

    def __init__(self, data=None, view_type=1):
        TreeView.__init__(self, enable_drag_drop=False,
                enable_multiple_select=True)

        # self.connect("double-click-item", self.on_music_view_double_click)
        # self.connect("press-return", self.on_music_view_press_return)
        # self.connect("right-press-items", self.on_music_view_right_press_items)
        event_manager.connect("update-song-tooltip",
                self.update_song_tooltip)

        self.db_file = get_cache_file("neteasecloudmusic/neteasecloudmusic.db")
        self.view_type = view_type
        self.view_data = data

        event_manager.connect("list-songs", self.list_songs)

        if self.view_type not in [self.PLAYING_LIST_TYPE, self.LOGIN_LIST_TYPE,
                self.PERSONAL_FM_ITEM]:
            self.load_onlinelist_songs()

        if self.view_type == self.PERSONAL_FM_ITEM:
            self.enable_multiple_select=False

    @property
    def items(self):
        return self.get_items()

    @property
    def playback_mode(self):
        return config.get("setting", "loop_mode")

    def update_song_tooltip(self, widget, text):
        self.set_tooltip_text(text)

    def clear_items(self):
        self.clear()

    def list_songs(self, songs, thread_id, **kwargs):
        self.clear_items();
        if thread_id != self.online_thread_id:
            return
        self.add_songs([Song(song) for song in songs])

    def draw_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutMiddle")

    # set self as current global playlist
    def set_current_source(self):
        if Player.get_source() != self:
            Player.set_source(self)

    def request_song(self, song, play=True):
        if song:
            self.set_highlight_song(song)
            cover_path = get_cache_file('cover')
            if not os.path.exists(cover_path):
                os.mkdir(cover_path)
            for the_file in os.listdir(cover_path):
                file_path = os.path.join(cover_path, the_file)
                try:
                    os.unlink(file_path)
                except:
                    pass
            url = nplayer.get_songs_url([song['sid']])[0]['url']
            nplayer.save_lyric(nplayer.get_lyric(song['sid']), song['sid'],
                    song['name'], song['artist'])
            if not url:
                self.get_next_song()
                return
            song['uri'] = url
            self.play_song(song, play=True)

    def pre_fetch_fm_songs(self):
        if (self.highlight_item and (self.highlight_item in self.items) and
                self.view_type == self.PERSONAL_FM_ITEM):
            current_index = self.items.index(self.highlight_item)
            if current_index >= len(self.items)-2:
                songs = [Song(song) for song in nplayer.personal_fm()]
                songs = [song for song in songs if (song['id'] not in
                    [exists_song['id'] for exists_song in self.get_songs()])]
                if songs:
                    count = len(self.items) + len(songs) - 17
                    if count > 0:
                        self.delete_items([self.items[i] for i in range(count)])
                    self.add_fm(songs)
                else:
                    self.pre_fetch_fm_songs()

    def play_song(self, song, play=False):
        if not song: return None

        # update song info
        self.update_songitem(song)

        # clear current select status
        del self.select_rows[:]
        self.queue_draw()

        # set item highlight
        self.set_highlight_song(song)

        if play:
            # play song now
            Player.play_new(song)

            # set self as current global playlist
            self.set_current_source()

            event_manager.emit("save-playing-status")
        self.pre_fetch_fm_songs()
        return song

    def get_songs(self):
        songs = []
        self.update_item_index()
        for song_item in self.items:
            songs.append(song_item.get_song())
        return songs

    def add_fm(self, songs, pos=None, sort=False, play=False):
        song_items = [SongItem(song) for song in songs]
        if song_items:
            if not self.items:
                self.emit_add_signal()
            self.add_items(song_items, pos, False)
            event_manager.emit("save-playing-status")

        if len(songs) >= 1 and play:
            song = songs[0]
            self.request_song(song, play=True)

    def add_songs(self, songs, pos=None, sort=False, play=False):
        if not songs:
            return

        if not isinstance(songs[0], Song):
            temp = []
            for song in songs:
                temp.append(Song(song))
            songs = temp

        song_items = [ SongItem(song) for song in songs if song.song_id not in
                [exists_song.song_id for exists_song in self.get_songs()]]

        if song_items:
            self.add_items(song_items, pos, False)

        if len(songs) >= 1 and play:
            song = songs[0]
            self.request_song(song, play=True)

    def set_highlight_song(self, song):
        if not song: return
        if SongItem(song) in self.items:
            self.set_highlight_item(self.items[self.items.index(SongItem(Song(song)))])
            self.visible_highlight()
            self.queue_draw()

    def update_songitem(self, song):
        if not song: return
        if song in self.items:
            self.items[self.items.index(SongItem(song))].update(song, True)

    def get_next_song(self, maunal=False):
        if len(self.items) <= 0:
            return

        if self.view_type == self.PERSONAL_FM_ITEM:
            self.get_next_fm()
            return

        if self.highlight_item:
            if self.highlight_item in self.items:
                current_index = self.items.index(self.highlight_item)
                if self.playback_mode == 'list_mode':
                    next_index = current_index + 1
                    if next_index > len(self.items) - 1:
                        next_index = 0
                elif self.playback_mode == 'single_mode':
                    next_index = current_index
                elif self.playback_mode == 'order_mode':
                    next_index = current_index + 1
                    if next_index > len(self.items) - 1:
                        return
                elif self.playback_mode == 'random_mode':
                    next_index = random.choice(
                            range(0, current_index)
                            +range(current_index+1, len(self.items)))
                highlight_item = self.items[next_index]
            else:
                highlight_item = self.items[0]
        else:
            highlight_item = self.items[0]
        self.request_song(highlight_item.get_song(), play=True)

    def get_next_fm(self):
        if self.highlight_item and self.highlight_item in self.items:
            current_index = self.items.index(self.highlight_item)
            next_index = current_index + 1
            if next_index > len(self.items) -1:
                return
            highlight_item = self.items[next_index]
        else:
            highlight_item = self.items[0]

        self.request_song(highlight_item.get_song(), play=True)

    def get_previous_song(self):
        if len(self.items) <= 0:
            return

        if self.view_type == self.PERSONAL_FM_ITEM:
            self.get_pervious_fm()
            return

        if self.highlight_item:
            if self.highlight_item in self.items:
                current_index = self.items.index(self.highlight_item)
                if self.playback_mode == 'list_mode':
                    pervious_song = current_index - 1
                    if pervious_song > len(self.items) - 1:
                        pervious_song = 0
                elif self.playback_mode == 'single_mode':
                    pervious_song = current_index
                elif self.playback_mode == 'order_mode':
                    pervious_song = current_index - 1
                    if pervious_song < 0:
                        return
                elif self.playback_mode == 'random_mode':
                    pervious_song = random.choice(
                            range(0, current_index)
                            +range(current_index+1, len(self.items)))
                highlight_item = self.items[pervious_song]
            else:
                highlight_item = self.items[0]
        else:
            highlight_item = self.items[0]

        self.request_song(highlight_item.get_song(), play=True)

    def get_pervious_fm(self):
        if self.highlight_item and self.highlight_item in self.items:
            current_index = self.items.index(self.highlight_item)
            privious_index = current_index - 1
            if privious_index < 0:
                return
            highlight_item = self.items[privious_index]
        else:
            highlight_item = self.items[0]

        self.request_song(highlight_item.get_song(), play=True)

    def dump_songs(self):
        return [ song.get_dict() for song in self.get_songs() ]

    @property
    def list_id(self):
        if self.view_data:
            try:
                playlist_id = self.view_data.get("id", "")
            except:
                playlist_id = ""
        else:
            playlist_id = ""

        return playlist_id

    @property
    def current_song(self):
        if self.highlight_item:
            return self.highlight_item.get_song()
        return None

music_view = MusicView()
