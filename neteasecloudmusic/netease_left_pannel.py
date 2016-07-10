#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
import copy
import pango

from widget.ui_utils import (draw_alpha_mask, switch_tab, draw_line)
from xdg_support import get_cache_file
from nls import _
from song import Song
from player import Player
from dtk.ui.threads import post_gui
from dtk.ui.treeview import IconTextItem
from dtk.ui.treeview import TreeView
from widget.skin import app_theme
from constant import CATEGROYLIST_WIDTH, HIDE_PLAYLIST_WIDTH
import utils

from netease_events import event_manager
from netease_music_view import music_view
from netease_music_playlist_item import PlaylistItem, CategoryListItem, PlayingListItem
from netease_music_player import neteasecloud_music_player as nplayer

class LeftPannel(gtk.VBox):
    def __init__(self):
        super(LeftPannel, self).__init__()

        # Set db file
        self.listen_db_file = get_cache_file("neteasecloudmusic/local_listen.db")

        # Set playinglist and personal FM item
        self.playing_list_item = PlayingListItem('播放列表',
                PlaylistItem.PLAYING_LIST_TYPE)
        self.personal_fm_item = PlayingListItem("私人FM",
                PlaylistItem.PERSONAL_FM_ITEM)
        self.created_list_item = CategoryListItem("创建的歌单",
                CategoryListItem.CREATED_LIST_TYPE)
        self.collected_list_item = CategoryListItem("收藏的歌单",
                CategoryListItem.COLLECTED_LIST_TYPE)

        self.playlist_view = PlaylistView(enable_drag_drop=False,
                enable_multiple_select=True)
        self.playlist_view.add_items([self.playing_list_item,
            self.personal_fm_item, self.created_list_item,
            self.collected_list_item])

        # Delete dtk "delete" key binding
        del self.playlist_view.keymap["Delete"]

        self.playlist_view.draw_mask = self.draw_playlist_list_mask
        self.playlist_view.set_size_request(CATEGROYLIST_WIDTH, -1)

        self.music_view = music_view
        # self.playlist_view.connect("single-click-item",
                # self.playing_list_item.expand)

        self.load_playlist_id = 0

        self.load()
        self.add(self.playlist_view)
        self.load_playlist()

    # Access playlist_view highlight_item
    current_item = property(lambda self: self.playlist_view.highlight_item)
    items = property(lambda self: self.playlist_view.visible_items)

    def draw_playlist_list_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutLeft")

    def switch_view(self, item):
        """ switch view_box's content """

        self.playlist_view.set_highlight_item(item)
        switch_tab(self.view_box, item.list_widget)

    def save(self, *args):
        if Player.get_source().showing_list_type == \
                music_view.PLAYING_LIST_TYPE:
            current_playing_item = 'playing_list'
        elif Player.get_source().showing_list_type == \
                music_view.PERSONAL_FM_ITEM:
            current_playing_item = 'personal_fm'
        else:
            current_playing_item = None

        playing_list_songs = self.playing_list_item.songs
        try:
            playing_list_song = self.playing_list_item.song_view.current_song.get_dict()
        except:
            playing_list_song = None

        personal_fm_songs = self.personal_fm_item.song_view.dump_songs()
        try:
            personal_fm_song = self.personal_fm_item.song_view.current_song.get_dict()
        except:
            personal_fm_song = None

        utils.save_db((current_playing_item,
            (playing_list_song, playing_list_songs),
            (personal_fm_song, personal_fm_songs)),
            self.listen_db_file)

    def load(self):
        try:
            objs = utils.load_db(self.listen_db_file)
            (current_playing_item,
                (playing_list_song, playing_list_songs),
                (personal_fm_song, personal_fm_songs)) = objs
            if current_playing_item == 'playing_list':
                self.current_playing_item = self.playing_list_item
                self.last_song = Song(playing_list_song)
            elif current_playing_item == 'personal_fm':
                self.current_playing_item = self.personal_fm_item
                self.last_song = Song(personal_fm_song)
            else:
                self.current_playing_item = None
                self.last_song = None
            self.playing_list_item.add_songs([Song(song) for song in
                playing_list_songs])
            if nplayer.is_login:
                self.personal_fm_item.add_songs([Song(song) for song in
                    personal_fm_songs])
        except:
            self.last_song = None
            utils.save_db(None, self.listen_db_file)
            return

    def load_playlist(self):
        self.load_playlist_id += 1
        thread_id = copy.deepcopy(self.load_playlist_id)
        utils.ThreadFetch(
                fetch_funcs=(nplayer.get_user_playlist, (nplayer.get_uid(),)),
                success_funcs=(self.render_online_lists, (thread_id,))
                ).start()
        pass

    def on_viewbox_size_allocate(self, widget, rect):
        ''' auto hide song_view's column when view_box's size changing '''

        if self.current_item:
            if rect.width > HIDE_PLAYLIST_WIDTH:
                self.current_item.song_view.set_hide_columns(None)
            else:
                self.current_item.song_view.set_hide_columns([1])

    @post_gui
    def render_online_lists(self, playlists, thread_id,
            current_playlist_id=None):
        if self.load_playlist_id != thread_id:
            return

        if len(playlists) > 0:
            items = [PlaylistItem(data, None, True, False) for data in playlists]
            self.created_list_item.add_items([item for item in items if
                item.list_type == PlaylistItem.FAVORITE_LIST_TYPE])
            self.created_list_item.add_items([item for item in items if
                item.list_type == PlaylistItem.CREATED_LIST_TYPE])
            self.collected_list_item.add_items([item for item in items if
                item.list_type == PlaylistItem.COLLECTED_LIST_TYPE])


class PlaylistView(TreeView):
    def add_items(self, items, insert_pos=None, clear_first=False):
        for item in items:
            song_view = getattr(item, "song_view", None)
            if song_view:
                setattr(song_view, "playlist_view", self)
        TreeView.add_items(self, items, insert_pos, clear_first)

    items = property(lambda self: self.visible_items)
