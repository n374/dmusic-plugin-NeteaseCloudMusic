#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gobject
import gtk
import copy

from dtk.ui.paned import HPaned
from dtk.ui.threads import post_gui
from dtk.ui.menu import Menu
from dtk.ui.dialog import InputDialog, ConfirmDialog
from deepin_utils.net import is_network_connected

import utils
from widget.skin import app_theme
from constant import CATEGROYLIST_WIDTH, HIDE_PLAYLIST_WIDTH
from widget.ui_utils import (draw_alpha_mask, switch_tab, draw_line)
from xdg_support import get_cache_file
from song import Song
from player import Player

from netease_events import event_manager
from netease_music_list_item import MusicListItem, nplayer
from netease_music_view import CategoryView

def login_required(func):
    """ Decorator. If not login, emit 'login-dialog-run', else run func() """
    def inner(*args, **kwars):
        if nplayer.is_login:
            return func(*args, **kwargs)
        else:
            event_manager.emit('login-dialog-run')
    return inner

class MusicPlaylist(gtk.VBox):
    #__gsignals__ = {
            #"login-success" :
                #(gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            #"empty-items" :
                #(gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
            #}

    def __init__(self):
        super(MusicPlaylist, self).__init__()

        # Set db file
        self.listen_db_file = get_cache_file("neteasecloudmusic/local_listen.db")
        self.status_db_file = get_cache_file("neteasecloudmusic/status.db")

        # Set default & collect list item
        self.playing_list_item = MusicListItem("播放列表")
        #self.created_list_item = MusicListItem("我的歌单",
                #list_type=MusicListItem.CREATED_LIST_TYPE,
                #has_separator=True)
        #self.collected_list_item = MusicListItem("收藏歌单",
                #list_type=MusicListItem.COLLECTED_LIST_TYPE,
                #has_separator=True)

        # Set category list and connect click/right click
        self.category_list = CategoryView(enable_drag_drop=False,
                enable_multiple_select=True)
        self.category_list.add_items([self.playing_list_item])

        del self.category_list.keymap["Delete"]
        self.category_list.draw_mask = self.draw_category_list_mask
        self.category_list.set_size_request(CATEGROYLIST_WIDTH, -1)
        self.category_list.connect("single-click-item",
                self.on_category_single_click)
        self.category_list.connect("right-press-items",
                self.on_category_right_press)
        #self.category_list.set_highlight_item(self.playing_list_item)

        # Set view_box
        self.view_box = gtk.VBox()
        self.view_box.connect("size-allocate",
                self.on_viewbox_size_allocate)
        #self.view_box.add(self.playing_list_item.list_widget)

        main_paned = HPaned(handle_color=app_theme.get_color("panedHandler"),
                enable_drag=True)
        main_paned.pack1(self.category_list, True, True)
        main_paned.pack2(self.view_box, True, False)

        """ Set events"""
        event_manager.connect("login-success", self.load_online_lists)
        event_manager.connect("relogin", self.relogin)
        event_manager.connect("add-and-play", self.add_and_play)
        event_manager.connect("add-to-playlist", self.add_to_playlist)
        #event_manager.connect("login-success",
                #self.on_event_login_success)
        #event_manager.connect("collect-songs",
                #self.on_event_collect_songs)
        #event_manager.connect("add-songs",
                #self.on_event_add_songs)
        #event_manager.connect("play-songs",
                #self.on_event_play_songs)
        #event_manager.connect("save-listen-lists",
                #self.on_event_save_listen_lists)
        #event_manager.connect("save-playlist-status",
                #self.save_status)

        # Load playlists
        self.online_thread_id = 0
        self.new_list_thread_id = 0

        #self.load()
        if nplayer.is_login:
            self.load_online_lists('')
        else:
            self.login_item = MusicListItem("登录", is_login_item=True)
            self.category_list.add_items([self.login_item])
        #self.load_status()

        self.add(main_paned)

    # Access category_list highlight_item
    current_item = property(lambda self: self.category_list.highlight_item)
    items = property(lambda self: self.category_list.visible_items)

    def add_and_play(self, *args):
        self.playing_list_item.song_view.add_songs(
                self.current_item.song_view.add_and_play_songs, play=True)

    def add_to_playlist(self, *args):
        self.playing_list_item.song_view.add_songs(
                self.current_item.song_view.add_and_play_songs, play=False)

    def load_status(self):
        obj = utils.load_db(self.status_db_file)
        if obj:
            index, d = obj
            song = Song()
            song.init_from_dict(d, cmp_key="sid")
        else:
            index = 0
            song = None

        self.playlist_index = index
        self.last_song = song

    def save_status(self, *args):
        index = 0
        player_source = Player.get_source()
        for i, item in enumerate(self.category_list.get_items()):
            if item.song_view == player_source:
                index = i

        try:
            song = self.current_item.current_song
            utils.save_db((index, song.get_dict()), self.status_db_file)
        except:
            pass

    def restore_status(self):
        try:
            target_item = self.items[self.playlist_index]
        except:
            target_item = None

        if target_item:
            self.switch_view(target_item)
            if is_network_connected():
                self.current_item.play_song(self.last_song, play=True)
    def draw_category_list_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutLeft")

    def on_category_single_click(self, widget, item, column, x, y):
        """ Switch view_box content when click category_list's item """

        if item:
            self.switch_view(item)

    def on_category_right_press(self, widget, x, y, item, column):
        menu_items = [
                #(None, "新建歌单", self.new_online_list),
                (None, "重新登录", self.relogin)
                ]
        if not item:
            Menu(menu_items, True).show((x, y))
            return

        if item.list_type == MusicListItem.COLLECT_TYPE:
            if nplayer.is_login:
                menu_items = [
                        (None, "刷新", item.refrush)
                        (None, "新建歌单", self.new_online_list),
                        ]
            else:
                menu_items = None

        elif item.list_type == MusicListItem.PLAYLIST_TYPE:
            menu_items = [
                    (None, "新建歌单", self.new_online_list),
                    (None, "删除歌单",
                        lambda : self.del_online_list(item)),
                    (None, "重命名",
                        lambda : self.rename_online_list(item)),
                    (None, "刷新", item.refrush),
                    ]

        elif item.list_type == MusicListItem.LOCAL_TYPE:
            menu_items.extend([
                (None, "删除列表",
                    lambda : self.del_listen_list(item)),
                (None, "重命名", lambda : self.rename_online_list(item,
                    is_online=False))
                ])

        if menu_items:
            Menu(menu_items, True).show((x, y))

    def relogin(self):
        nplayer.relogin()
        self.category_list.delete_items([item for item in self.items if
            item.list_type!=MusicListItem.PLAYING_LIST_TYPE])
        self.login_item = MusicListItem("登录", is_login_item=True)
        self.category_list.add_items([self.login_item])
        self.switch_view(self.login_item)

    def switch_view(self, item):
        """ switch view_box's content """

        self.category_list.set_highlight_item(item)
        switch_tab(self.view_box, item.list_widget)

    def save(self):
        local_lists = filter(
                lambda item: item.list_type == MusicListItem.LOCAL_TYPE,
                self.items)
        if len(local_lists) > 0:
            objs = [item.dump_list() for item in local_lists]
            utils.save_db(objs, self.listen_db_file)

    def load(self):
        objs = utils.load_db(self.listen_db_file)
        if objs:
            items = []
            for title, nsongs in bojs:
                item = MusicListItem(title, list_type=MusicListItem.LOCAL_TYPE)
                songs = []
                for d in nsongs:
                    s = Song()
                    s.init_from_dict(d, cmp_key="sid")
                    songs.append(s)
                item.add_songs(songs)
                items.append(item)
            self.category_list.add_items(items, insert_pos=1)

    def del_listen_list(self, item):
        def del_list():
            if self.current_item == item:
                self.switch_view(self.default_list_item)
            self.category_list.delete_items([item])
            self.save()

        ConfirmDialog("提示", "您确定要删除【%s】列表么？" % item.title,
                confirm_callback=del_list).show_all()

    def on_viewbox_size_allocate(self, widget, rect):
        ''' auto hide song_view's column when view_box's size changing '''

        if self.current_item:
            if rect.width > HIDE_PLAYLIST_WIDTH:
                self.current_item.song_view.set_hide_columns(None)
            else:
                self.current_item.song_view.set_hide_columns([1])

    def on_event_login_success(self, obj, data):
        """ load online playlists when user login success """

        self.load_online_lists()

    def on_event_collect_songs(self, obj, data):
        self.collect_list_item.add_songs(data, pos=0)

    def on_event_add_songs(self, obj, data):
        self.add_play_songs(data)

    def on_event_play_songs(self, obj, data):
        self.add_play_songs(data, play=True)

    def on_event_save_listen_lists(self, obj, data):
        self.save()

    def add_play_songs(self, data, play=False):
        if self.current_item.list_type not in (MusicListItem.DEFAULT_TYPE,
                MusicListItem.LOCAL_TYPE):
            self.switch_view(self.default_list_item)

        self.current_item.add_songs(data, play=play)

    def load_online_lists(self, args, *kwargs):
        try:
            self.category_list.delete_items([item for item in self.items if
                item.list_type!=MusicListItem.PLAYING_LIST_TYPE])
        except:
            pass
        self.online_thread_id += 1
        thread_id = copy.deepcopy(self.online_thread_id)

        utils.ThreadFetch(
                fetch_funcs=(nplayer.user_playlist, (nplayer.uid,)),
                success_funcs=(self.render_online_lists, (thread_id,))
                ).start()

    @post_gui
    def render_online_lists(self, playlists, thread_id):
        if self.online_thread_id != thread_id:
            return

        if len(playlists) > 0:
            items = [MusicListItem(data, True) for data in playlists]
            self.category_list.add_items(items)

    def del_online_list(self, item):
        def nplayer_del_list():
            nplayer_del_list(item.list_id)
            if self.current_item == item:
                self.switch_view(self.default_list_item)
            self.category_list.delete_items([item])

        ConfirmDialog("提示", "您确定要删除【%s】歌单吗？" % item.title,
                confirm_callback=nplayer_del_list).show_all()

    @login_required
    def new_online_list(self):
        def nplayer_new_list(name):
            self.new_list_thread_id += 1
            thread_id = copy.deepcopy(self.new_list_thread_id)
            utils.ThreadFetch(
                    fetch_funcs=(nplayer.new_list, (name,)),
                    success_funcs=(self.render_new_online_list, (thread_id,))
                    ).start()

        input_dialog = InputDialog("新建歌单", "", 300, 100, nplayer_new_list)
        input_dialog.show_all()

    @post_gui
    def render_new_online_list(self, data, thread_id):
        if self.new_list_thread_id != thread_id:
            return
        item = MusicListItem(data)
        self.category_list.add_items([item])

    def rename_online_list(self, item, is_online=True):
        def nplayer_rename_list(name):
            if name.strip():
                item.set_title(name)
                if is_online:
                    nplayer.rename_list(item.list_id, name)
                else:
                    self.save()
        input_dialog = InputDialog("重命名歌单", item.title, 300, 100,
                nplayer_rename_list)
        input_dialog.show_all()
