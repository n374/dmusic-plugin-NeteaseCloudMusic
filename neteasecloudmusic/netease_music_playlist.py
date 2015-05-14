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
from nls import _
from song import Song
from player import Player

from netease_events import event_manager
from netease_music_list_item import MusicListItem, nplayer
from netease_music_view import CategoryView
from netease_music_view import MusicView
from netease_music_browser import SongView

def login_required(func):
    """ Decorator. If not login, emit 'login-dialog-run', else run func() """
    def inner(*args, **kwargs):
        if nplayer.is_login:
            return func(*args, **kwargs)
        else:
            event_manager.emit('login-dialog-run')
    return inner

class MusicPlaylist(gtk.VBox):
    def __init__(self):
        super(MusicPlaylist, self).__init__()

        # Set db file
        self.listen_db_file = get_cache_file("neteasecloudmusic/local_listen.db")
        self.status_db_file = get_cache_file("neteasecloudmusic/status.db")

        # Set default & collect list item
        self.playing_list_item = MusicListItem("播放列表",
                MusicListItem.PLAYING_LIST_TYPE)
        self.personal_fm_item = MusicListItem("私人FM",
                MusicListItem.PERSONAL_FM_ITEM)

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
        event_manager.connect("add-songs-to-playing-list",
                self.add_songs_to_playing_list)
        event_manager.connect("save-playing-status",
                self.save)
        event_manager.connect("favorite-list-refreshed",
                self.favorite_list_refreshed)
        event_manager.connect("refresh-favorite-list",
                self.refresh_favorite_list)
        event_manager.connect("refresh-online-list", self.refresh_online_list)
        event_manager.connect("refresh-online-lists", self.refresh_online_lists)

        # Load playlists
        self.online_thread_id = 0
        self.new_list_thread_id = 0

        self.load()

        if nplayer.is_login:
            self.load_online_lists('')
        else:
            self.login_item = MusicListItem("登录",
                    MusicListItem.LOGIN_LIST_TYPE)
            self.category_list.add_items([self.login_item])

        self.add(main_paned)

    # Access category_list highlight_item
    current_item = property(lambda self: self.category_list.highlight_item)
    items = property(lambda self: self.category_list.visible_items)

    def add_songs_to_playing_list(self, obj, (songs, play)):
        self.playing_list_item.song_view.add_songs(songs, play=play)
        self.save()

    def restore_status(self):
        try:
            target_item = self.current_playing_item
        except:
            target_item = None

        if target_item:
            self.switch_view(target_item)
            if is_network_connected():
                self.current_item.play_song(self.last_song, play=True)

    def favorite_list_refreshed(self, obj, songs):
        # 将“我喜欢的音乐”中的歌曲传递给MusicView，以方便判断哪些歌曲已被红心
        MusicView.FAVORITE_SONGS = [song['id'] for song in songs]

    def refresh_favorite_list(self, *kwargs):
        for item in self.category_list.items:
            if item.list_type == MusicListItem.FAVORITE_LIST_TYPE:
                item.song_view.load_onlinelist_songs()
                break

    def refresh_online_list(self, obj, playlist_id):
        for item in self.category_list.items:
            if item.list_id == playlist_id:
                item.song_view.load_onlinelist_songs()
                break

    def draw_category_list_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutLeft")

    def on_category_single_click(self, widget, item, column, x, y):
        """ Switch view_box content when click category_list's item """

        if item:
            self.switch_view(item)

    def on_category_right_press(self, widget, x, y, item, column):
        relogin_submenu = Menu([(None, _("确定"), self.relogin)])
        menu_items = [
                (None, _("刷新歌单"), self.refresh_online_lists),
                (None, _("重新登录"), relogin_submenu),
                ]
        if item:
            self.right_clicked_item = item
            if item.list_type == MusicListItem.PLAYING_LIST_TYPE:
                pass
            elif item.list_type == MusicListItem.CREATED_LIST_TYPE:
                pass
            elif item.list_type == MusicListItem.COLLECTED_LIST_TYPE:
                unsubscribe_playlist_submenu = [
                        (None, _('**确定删除**'),
                    self.unsubscribe_playlist, item.list_id),
                        (None, _(item.title), self.unsubscribe_playlist,
                            item.list_id),
                        (None, _('**确定删除**'),
                    self.unsubscribe_playlist, item.list_id)]
                menu_items.insert(1, (None, _('删除歌单'),
                    Menu(unsubscribe_playlist_submenu)))
            elif item.list_type == MusicListItem.FAVORITE_LIST_TYPE:
                pass

        if menu_items:
            Menu(menu_items, True).show((x, y))

    def add_list_to_playing_list(self):
        self.playing_list_item.song_view.add_songs(
                self.right_clicked_item.song_view.get_songs(), play=False)
        self.save()

    def add_list_to_playing_list_and_play(self):
        self.playing_list_item.song_view.add_songs(
                self.right_clicked_item.song_view.get_songs(), play=True)
        self.save()

    def unsubscribe_playlist(self, playlist_id):
        if nplayer.unsubscribe_playlist(playlist_id):
            self.refresh_online_lists()

    def relogin(self):
        nplayer.relogin()
        self.personal_fm_item.song_view.delete_all_items()
        self.category_list.delete_items([item for item in self.items if
            item.list_type!=MusicListItem.PLAYING_LIST_TYPE])
        self.login_item = MusicListItem("登录", MusicListItem.LOGIN_LIST_TYPE)
        self.category_list.add_items([self.login_item])
        self.switch_view(self.login_item)

    def switch_view(self, item):
        """ switch view_box's content """

        self.category_list.set_highlight_item(item)
        switch_tab(self.view_box, item.list_widget)

    def save(self, *args):
        if Player.get_source() == self.playing_list_item.song_view:
            current_playing_item = 'playing_list'
        elif Player.get_source() == self.personal_fm_item.song_view:
            current_playing_item = 'personal_fm'
        else:
            current_playing_item = None

        playing_list_songs = self.playing_list_item.song_view.dump_songs()
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

    def on_event_collect_songs(self, obj, data):
        self.collect_list_item.add_songs(data, pos=0)

    def on_event_add_songs(self, obj, data):
        self.add_play_songs(data)

    def on_event_play_songs(self, obj, data):
        self.add_play_songs(data, play=True)

    def on_event_save_listen_lists(self, obj, data):
        self.save()

    #def add_play_songs(self, data, play=False):
        #if self.current_item.list_type not in (MusicListItem.DEFAULT_TYPE,
                #MusicListItem.LOCAL_TYPE):
            #self.switch_view(self.default_list_item)

        #self.current_item.add_songs(data, play=play)

    def refresh_online_lists(self, *kwargs):
        if self.category_list.highlight_item:
            current_playlist_id = self.category_list.highlight_item.song_view.list_id
        try:
            self.category_list.delete_items([item for item in self.items if
                item.list_type not in
                [MusicListItem.PLAYING_LIST_TYPE, MusicListItem.PERSONAL_FM_ITEM]])
        except:
            pass

        self.online_thread_id += 1
        thread_id = copy.deepcopy(self.online_thread_id)

        utils.ThreadFetch(
                fetch_funcs=(nplayer.user_playlist, (nplayer.get_uid(),)),
                success_funcs=(self.render_online_lists, (thread_id,
                    current_playlist_id))
                ).start()

    def load_online_lists(self, args, *kwargs):
        try:
            self.category_list.delete_items([item for item in self.items if
                item.list_type!=MusicListItem.PLAYING_LIST_TYPE])
        except:
            pass

        self.category_list.add_items([self.personal_fm_item])
        self.online_thread_id += 1
        thread_id = copy.deepcopy(self.online_thread_id)

        # Get personal FM songs
        while len(self.personal_fm_item.song_view.items) < 2:
            songs = nplayer.personal_fm()
            self.personal_fm_item.add_songs([Song(song) for song in songs])

        utils.ThreadFetch(
                fetch_funcs=(nplayer.user_playlist, (nplayer.get_uid(),)),
                success_funcs=(self.render_online_lists, (thread_id,))
                ).start()

    @post_gui
    def render_online_lists(self, playlists, thread_id,
            current_playlist_id=None):
        MusicView.CREATED_LISTS_DICT = {playlist['name']:playlist['id'] for playlist
                in playlists if not playlist['subscribed']}
        SongView.CREATED_LISTS_DICT = {playlist['name']:playlist['id'] for playlist
                in playlists if not playlist['subscribed']}
        if self.online_thread_id != thread_id:
            return

        if len(playlists) > 0:
            items = [MusicListItem(data, None, True) for data in playlists]
            self.category_list.add_items(items)

        if current_playlist_id and current_playlist_id in [item.song_view.list_id for item in self.category_list.items]:
            current_item=[item for item in self.category_list.items if
                    item.list_id==current_playlist_id][0]
            self.category_list.set_highlight_item(current_item)
            self.switch_view(current_item)
        else:
            self.category_list.set_highlight_item(self.playing_list_item)
            self.switch_view(self.playing_list_item)

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
        item = MusicListItem(data, None, True)
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
