#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gobject
import copy
import time

from dtk.ui.treeview import TreeView
from dtk.ui.threads import post_gui
from dtk.ui.menu import Menu

from widget.ui_utils import draw_alpha_mask
from widget.song_item import SongItem
from player import Player

import utils
from xdg_support import get_cache_file
from nls import _
from song import Song

from netease_music_player import neteasecloud_music_player as nplayer
from netease_events import event_manager

class CategoryView(TreeView):
    def add_items(self, items, insert_pos=None, clear_first=False):
        for item in items:
            song_view = getattr(item, "song_view", None)
            if song_view:
                setattr(song_view, "category_view", self)
        TreeView.add_items(self, items, insert_pos, clear_first)

    items = property(lambda self: self.visible_items)

class MusicView(TreeView):
    PLAYING_LIST_TYPE = 1
    FAVORITE_LIST_TYPE = 2
    CREATED_LIST_TYPE = 3
    COLLECTED_LIST_TYPE = 4
    LOGIN_LIST_TYPE = 5

    __gsignals__ = {
            "begin-add-items" :
                (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            "empty-items" :
                (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
            }

    def __init__(self, data=None, view_type=1):
        TreeView.__init__(self, enable_drag_drop=False,
                enable_multiple_select=True)

        # view_type 为list类型
        self.connect("double-click-item", self.on_music_view_double_click)
        self.connect("press-return", self.on_music_view_press_return)
        self.connect("right-press-items", self.on_music_view_right_press_items)
        #self.connect("delete-select-items",
                #self.on_music_view_delete_select_items)

        self.db_file = get_cache_file("neteasecloudmusic/neteasecloudmusic.db")
        self.view_type = view_type
        self.view_data = data

        self.request_thread_id = 0
        self.collect_thread_id = 0
        self.onlinelist_thread_id = 0
        self.collect_page = 0

        #self.load_online_playlists()
        #if self.view_type == self.DEFAULT_TYPE:
            #self.load()
        #elif self.view_type == self.COLLECT_TYPE:
            #self.load_collect_songs()
        #elif self.view_type == self.PLAYLIST_TYPE:
        self.load_onlinelist_songs()

    @property
    def items(self):
        return self.get_items()

    def on_music_view_double_click(self, widget, item, column, x, y):
        if item:
            song = item.get_song()
            if self.view_type==self.PLAYING_LIST_TYPE:
                self.request_song(song, play=True)
            else:
                self.add_play_emit([song])

    def on_music_view_press_return(self, widget, items):
        if items:
            if self.view_type==self.PLAYING_LIST_TYPE:
                song = items[0].get_song()
                self.request_song(song, play=True)
            else:
                songs = [item.get_song() for item in items]
                self.add_play_emit(songs)

    def add_play_emit(self, songs):
        self.add_and_play_songs = songs
        event_manager.emit('add-songs-to-playing-list-and-play')

    def add_to_playlist(self, songs):
        self.add_and_play_songs = songs
        event_manager.emit('add-songs-to-playing-list')

    def on_music_view_right_press_items(self, widget, x, y,
            current_item, select_items):
        if current_item and select_items:
            if self.view_type == self.PLAYING_LIST_TYPE:
                if len(select_items) > 1:
                    items = [
                            (None, _("Play"), lambda: self.add_play_emit(
                                [item.get_song() for item in select_items])),
                            (None, _("Delete"), lambda:
                                self.delete_items(select_items)),
                            (None, _("Clear List"), lambda: self.clear_items())
                            ]
                else:
                    items = [
                            (None, _("Play"), lambda:
                                self.add_play_emit([current_item.get_song()])),
                            (None, _("Delete"), lambda:
                                self.delete_items([select_items])),
                            (None, _("Clear List"), lambda: self.clear_items())
                            ]
            if self.view_type in [self.FAVORITE_LIST_TYPE,
                    self.COLLECTED_LIST_TYPE, self.CREATED_LIST_TYPE]:
                if len(select_items) > 1:
                    items = [
                            (None, _("Add"), lambda: self.add_to_playlist(
                                [item.get_song() for item in select_items])),
                            (None, _("Add and Play"), lambda: self.add_play_emit(
                                [item.get_song() for item in select_items])),
                            #(None, _("Delete"), lambda:
                                #self.delete_items(select_items)),
                            #(None, _("Clear List"), lambda: self.clear_items())
                            ]
                else:
                    items = [
                            (None, _("Add"), lambda:
                                self.add_to_playlist([current_item.get_song()])),
                            (None, _("Add and Play"), lambda:
                                self.add_play_emit([current_item.get_song()])),
                            #(None, _("Delete"), lambda:
                                #self.delete_items([select_items])),
                            #(None, _("Clear List"), lambda: self.clear_items())
                            ]


                #if self.view_type != self.PLAYLIST_TYPE and nplayer.is_login:
                    #sub_menu = self.get_add_online_list_menu(select_items)

                    #if sub_menu:
                        #items.insert(1, (None, "添加到歌单", sub_menu))

                    #if self.view_type != self.COLLECT_TYPE:
                        #favourite_items = filter(lambda item: item.list_type ==
                                #self.COLLECT_TYPE, self.category_view.items)
                        #if len(favourite_items) > 0:
                            #favourite_item = favourite_items[0]
                            #songs = [item.song for item in select_items]
                            #sids = self.get_sids(favourite_items)

                            #def add_to_favourite(item, songs, sids):
                                #item.add_songs(songs, pos=0)
                                #nplayer.add_favourite_song(sids)

                            #items.insert(1, (None, "喜欢", add_to_favourite,
                                #favourite_item, songs, sids))

            Menu(items, True).show((int(x), int(y)))

    def get_sids(self, items):
        return ",".join([str(item.song['sid']) for item in items if
            item.song.get('sid', None)])

    def get_add_online_list_menu(self, select_items):
        category_items = [item for item in self.category_view.items if
                item.list_type == self.PLAYLIST_TYPE]
        if len(category_items) <= 0:
            return None

        songs = [item.song for item in select_items]
        sids = self.get_sids(select_items)

        def add_song_to_list(item, songs, sids):
            item.add_songs(songs, pos=0)
            pid = item.list_id
            nplayer.add_list_song(pid, sids)

        munu_items = [(None, item.title, add_song_to_list, item, songs, sids)
                for item in category_items]
        return Menu(menu_items)

    def on_music_view_delete_select_items(self, widget, items):
        if not items:
            return

        #sids = self.get_sids(items)

        #if self.view_type == self.COLLECT_TYPE:
            #nplayer.del_collect_song(sids)

        #elif self.view_type == self.PLAYLIST_TYPE:
            #nplayer.del_list_song(self.list_id, sids)

        #elif self.view_type == self.DEFAULT_TYPE:
            #self.save()

        #elif self.view_type == self.LOCAL_TYPE:
            #event_manager.emit("save-listen-lists")

    def clear_items(self):
        self.clear()
        event_manager.emit("save-playing-list")

    def draw_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutMiddle")

    # set self as current global playlist
    def set_current_source(self):
        if Player.get_source() != self:
            Player.set_source(self)

    def emit_add_signal(self):
        self.emit("begin-add-items")

    def request_song(self, song, play=True):
        if self.adjust_uri_expired(song):
            self.request_thread_id += 1
            thread_id = copy.deepcopy(self.request_thread_id)
            utils.ThreadFetch(
                fetch_funcs=(nplayer.song_detail, (song['sid'],)),
                success_funcs=(self.render_play_song, (play, thread_id))
                ).start()
        else:
            self.play_song(song, play=True)

    def adjust_uri_expired(self, song):
        expire_time = song.get("uri_expire_time", None)
        duration = song.get("#duration", None)
        fetch_time = song.get("fetch_time", None)
        if not expire_time or not duration or not fetch_time or not song.get("uri", None):
            return True
        now = time.time()
        past_time = now - fetch_time
        if past_time > (expire_time - duration) / 1000 :
            return True
        return False

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

            event_manager.emit("save-playlist-status")
        return song

    @post_gui
    def render_play_song(self, song, play, thread_id):
        if thread_id != self.request_thread_id:
            return

        song["fetch_time"] = time.time()
        self.play_song(Song(song), play)

    def get_playlist_songs(self):
        songs = []
        self.update_item_index()
        for song_item in self.items:
            songs.append(song_item.get_song())
        return songs

    def load_online_playlists(self, clear=False):
        if clear:
            self.clear()

        if not nplayer.is_login:
            return
        self.collect_thread_id += 1
        thread_id = copy.deepcopy(self.collect_thread_id)
        utils.ThreadFetch(
            fetch_funcs=(nplayer.get_collect_songs, (self.collect_page,)),
            success_funcs=(self.render_collect_songs, (thread_id,))
            ).start()

    def get_songs(self):
        songs = []
        self.update_item_index()
        for song_item in self.items:
            songs.append(song_item.get_song())
        return songs

    def add_songs(self, songs, pos=None, sort=False, play=False):
        if not songs:
            return

        song_items = [ SongItem(song) for song in songs if song not in
                self.get_playlist_songs() ]

        if song_items:
            if not self.items:
                self.emit_add_signal()
            self.add_items(song_items, pos, False)

             #save songs
            #if self.view_type == self.DEFAULT_TYPE:
                #self.save()
            #if self.view_type == self.LOCAL_TYPE:
                #event_manager.emit("save-listen-lists")

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

        if self.highlight_item:
            if self.highlight_item in self.items:
                current_index = self.items.index(self.highlight_item)
                next_index = current_index + 1
                if next_index > len(self.items) - 1:
                    next_index = 0
                highlight_item = self.items[next_index]
            else:
                highlight_item = self.items[0]
        else:
            highlight_item = self.items[0]

        self.request_song(highlight_item.get_song(), play=True)

    def get_previous_song(self):
        if len(self.items) <= 0:
            return

        if self.highlight_item != None:
            if self.highlight_item in self.items:
                current_index = self.items.index(self.highlight_item)
                prev_index = current_index - 1
                if prev_index < 0:
                    prev_index = len(self.items) - 1
                highlight_item = self.items[prev_index]
        else:
            highlight_item = self.items[0]

        self.request_song(highlight_item.get_song(), play=True)

    def dump_songs(self):
        return [ song.get_dict() for song in self.get_songs() ]

    #def save(self):
        #objs = self.dump_songs()
        #utils.save_db(objs, self.db_file)

    #def load(self):
        #objs = utils.load_db(self.db_file)
        #songs = []
        #if objs:
            #for obj in objs:
                #s = Song()
                #s.init_from_dict(obj, cmp_key="sid")
                #songs.append(s)
        #if songs:
            #self.add_songs(songs)

    @post_gui
    def render_collect_songs(self, data, thread_id):
        if self.collect_thread_id != thread_id:
            return
        if len(data) == 2:
            songs, havemore = data
            self.add_songs(songs)

    def load_onlinelist_songs(self, clear=False):
        if clear:
            self.clear()

        if not nplayer.is_login:
            return

        if not self.view_data:
            print 'not self.view_data'
            return

        playlist_id = self.list_id

        self.onlinelist_thread_id += 1
        thread_id = copy.deepcopy(self.onlinelist_thread_id)
        utils.ThreadFetch(
            fetch_funcs=(nplayer.playlist_detail, (playlist_id,)),
            success_funcs=(self.render_onlinelist_songs, (thread_id,))
            ).start()

    @post_gui
    def render_onlinelist_songs(self, songs, thread_id):
        if self.onlinelist_thread_id != thread_id:
            return

        if songs:
            self.add_songs([Song(song) for song in songs])

    def refrush(self):
        if self.view_type == self.COLLECT_TYPE:
            self.load_collect_songs(clear=True)
        elif self.view_type == self.PLAYLIST_TYPE:
            self.load_onlinelist_songs(clear=True)

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
