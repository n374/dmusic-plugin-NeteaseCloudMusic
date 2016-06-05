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
from widget.skin import app_theme
from constant import CATEGROYLIST_WIDTH, HIDE_PLAYLIST_WIDTH
import utils

from netease_events import event_manager
from netease_music_view import PlaylistView
from netease_music_playlist_item import PlaylistItem, CategoryListItem
from netease_music_player import neteasecloud_music_player as nplayer

class LeftPannel(gtk.VBox):
    def __init__(self):
        super(LeftPannel, self).__init__()

        # Set db file
        self.listen_db_file = get_cache_file("neteasecloudmusic/local_listen.db")

        # Set playinglist and personal FM item
        self.playing_list_item = PlaylistItem('播放列表',
                PlaylistItem.PLAYING_LIST_TYPE)
        self.personal_fm_item = PlaylistItem("私人FM",
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

    def load(self):
            return

    def load_playlist(self):
        self.load_playlist_id += 1
        thread_id = copy.deepcopy(self.load_playlist_id)
        utils.ThreadFetch(
                fetch_funcs=(nplayer.user_playlist, (nplayer.get_uid(),)),
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
            items = [PlaylistItem(data, None, True) for data in playlists]
            for item in playlists:
                print item
            self.created_list_item.add_items([item for item in items if
                item.list_type == PlaylistItem.CREATED_LIST_TYPE])
            self.collected_list_item.add_items([item for item in items if
                item.list_type == PlaylistItem.COLLECTED_LIST_TYPE])