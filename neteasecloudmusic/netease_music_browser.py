#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
from dtk.ui.browser import WebView

from widget.ui import NetworkConnectFailed
from dtk.ui.dialog import DialogBox, DIALOG_MASK_MULTIPLE_PAGE
from HTMLParser import HTMLParser

from deepin_utils.net import is_network_connected
from netease_music_player import neteasecloud_music_player, player_interface
from netease_music_player import neteasecloud_music_player as nplayer
from netease_music_tools import get_cookie_file

from netease_events import event_manager

from player import Player
from widget.skin import app_theme
from dtk.ui.treeview import TreeItem, TreeView
from widget.ui_utils import (draw_single_mask, switch_tab,
                             draw_alpha_mask, render_item_text)
from dtk.ui.draw import draw_text
from dtk.ui.utils import get_content_size
from dtk.ui.menu import Menu
from song import Song
import utils
import pango
import gobject
from nls import _
DEFAULT_FONT_SIZE = 8
class MusicBrowser(gtk.VBox):
    def __init__(self):
        super(MusicBrowser, self).__init__(False)
        from widget.completion_window import search_entry
        # 将自带搜索框删除
        for anything in search_entry.get_children():
            search_entry.remove(anything)

        self.search_box = gtk.HBox(False)
        self.result_box = gtk.HBox(False)

        self.search_entry = gtk.Entry()
        self.search_entry.connect('activate', self.search)
        self.search_entry.set_size_request(438, 32)

        self.search_combobox = gtk.combo_box_new_text()
        self.combobox_item = ['歌曲', '歌单', '推荐']
        for item in self.combobox_item:
            self.search_combobox.append_text(item)
        self.search_combobox.set_active(0)
        self.search_combobox.set_size_request(-1, 32)
        self.search_combobox.connect('changed', self.change_search_type)

        self.search_button = gtk.Button("Search")
        self.search_button.connect('pressed', self.search)
        self.search_button.set_size_request(-1, 32)

        self.song_list = SongView()
        self.playlist_list = PlaylistView(enable_multiple_select=False)
        #self.playlist_list.connect('single-click-item', self.single_click_item)

        self.search_box.pack_start(self.search_combobox, False, False)
        self.search_box.pack_start(self.search_entry, False, False)
        self.search_box.pack_end(self.search_button, False, False)
        self.result_box.pack_start(self.playlist_list)
        self.result_box.pack_start(self.song_list)

        self.pack_start(self.search_box, False, False, 0)
        self.pack_end(self.result_box)
        self.show_all()

    def search(self, *kwargs):
        string = self.search_entry.get_text()
        index = self.search_combobox.get_active()
        if index == 2:
                switch_tab(self.result_box, self.song_list)
                self.song_list.add_items([SearchSongItem(Song(song))
                                          for song in
                                          nplayer.recommend_songlist()],
                                         clear_first=True)
        if string:
            if index == 0:
                switch_tab(self.result_box, self.song_list)
                self.song_list.add_items([SearchSongItem(Song(song)) for song in
                    nplayer.search(string)], clear_first=True)
            elif index == 1:
                switch_tab(self.result_box, self.playlist_list)
                self.playlist_list.add_items([PlaylistItem(playlist) for
                    playlist in nplayer.search(string, 1000)], clear_first=True)

    def change_search_type(self, obj):
        index = self.search_combobox.get_active()
        if index == 2:
                switch_tab(self.result_box, self.song_list)
                self.song_list.add_items([SearchSongItem(Song(song))
                                          for song in
                                          nplayer.recommend_songlist()],
                                         clear_first=True)
        string = self.search_entry.get_text()
        if string:
            if index == 0:
                switch_tab(self.result_box, self.song_list)
                self.song_list.add_items([SearchSongItem(Song(song))
                                          for song in nplayer.search(string)],
                                         clear_first=True)
            elif index == 1:
                switch_tab(self.result_box, self.playlist_list)
                self.playlist_list.add_items([PlaylistItem(playlist)
                                              for playlist in
                                              nplayer.search(string, 1000)],
                                             clear_first=True)

    def single_click_item(self, widget, item, column, x, y):
        self.result_box.add(self.song_list)

class PlaylistItem(TreeItem):
    def __init__(self, data):
        TreeItem.__init__(self)

        self.update(data, True)
        self.height = 26
        self.is_highlight = False

    def update(self, playlist, redraw=False):
        '''update'''
        self.playlist = playlist
        self.list_id = playlist['id']
        self.title = playlist["name"]
        self.creator = playlist["creator"]['nickname']
        self.count = playlist["trackCount"]

        # Calculate item size.
        self.title_padding_x = 15
        self.title_padding_y = 5
        (self.title_width, self.title_height) = get_content_size(self.title, DEFAULT_FONT_SIZE)

        self.creator_padding_x = 10
        self.creator_padding_y = 5
        (self.creator_width, self.creator_height) = get_content_size(self.creator, DEFAULT_FONT_SIZE)

        self.count_padding_x = 2
        self.count_padding_y = 5
        (self.count_width, self.count_height) = get_content_size(str(self.count), DEFAULT_FONT_SIZE)
        if redraw:
            self.emit_redraw_request()

    @property
    def get_playlist_id(self):
        return self.list_id

    @property
    def get_playlist(self):
        return self.playlist

    def get_height(self):
        return self.height

    def get_column_renders(self):
        return (self.render_title,)

    def emit_redraw_request(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def set_title(self, title):
        self.title = title
        self.emit_redraw_request()

    def render_title(self, cr, rect):
        '''Render title.'''
        if self.is_highlight:
            draw_single_mask(cr, rect.x + 1, rect.y, rect.width, rect.height, "globalItemHighlight")
        elif self.is_select:
            draw_single_mask(cr, rect.x + 1, rect.y, rect.width, rect.height, "globalItemSelect")
        elif self.is_hover:
            draw_single_mask(cr, rect.x + 1, rect.y, rect.width, rect.height, "globalItemHover")

        # if self.is_highlight:
        #     text_color = "#ffffff"
        # else:
        #     text_color = app_theme.get_color("labelText").get_color()

        rect.x += self.title_padding_x
        rect.width -= self.title_padding_x * 2
        render_item_text(cr, self.title, rect, self.is_select, self.is_highlight)

    def render_count(self, cr, rect):
        '''Render artist.'''
        if self.is_highlight:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHighlight")
        elif self.is_select:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemSelect")
        elif self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")


        rect.x += self.creator_padding_x
        rect.width -= self.creator_padding_x * 2
        render_item_text(cr, self.count, rect, self.is_select, self.is_highlight)

    def render_creator(self, cr, rect):
        '''Render length.'''
        if self.is_highlight:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHighlight")
        elif self.is_select:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemSelect")
        elif self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")


        rect.width -= self.creator_padding_x * 2
        rect.x += self.creator_padding_x * 2
        render_item_text(cr, self.creator, rect, self.is_select, self.is_highlight)

    def get_column_renders(self):
        '''Get render callbacks.'''
        return (self.render_title, self.render_count, self.render_creator)

    def get_column_widths(self):
        '''Get sizes.'''
        #if self.extend:
            #return (100, 100, 100, 90)
        #else:
            #return (156, 102, 51)
        return (160, 50, 101)

    def unselect(self):
        self.is_select = False
        self.emit_redraw_request()

    def select(self):
        self.is_select = True
        self.emit_redraw_request()

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        self.emit_redraw_request()

    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.emit_redraw_request()

    def highlight(self):
        self.is_highlight = True
        self.emit_redraw_request()

    def unhighlight(self):
        self.is_highlight = False
        self.emit_redraw_request()

class PlaylistView(TreeView):
    __gsignals__ = {
            "begin-add-items" :
                (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            "empty-items" :
                (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
            }

    def __init__(self, enable_multiple_select=True):
        TreeView.__init__(self, enable_drag_drop=False,
                enable_multiple_select=enable_multiple_select)

        #self.connect("double-click-item", self.on_music_view_double_click)
        #self.connect("press-return", self.on_music_view_press_return)
        self.connect("right-press-items", self.right_press_items)

    @property
    def items(self):
        return self.get_items()

    def right_press_items(self, widget, x, y,
            current_item, select_items):
        if current_item and select_items and nplayer.is_login:
            title = gobject.markup_escape_text(current_item.get_playlist['name'])
            subscribe_submenu = [
                    (None, _('**确定收藏**'), self.subscribe_playlist,
                current_item),
                    (None, _(title), self.subscribe_playlist, current_item),
                    (None, _('**确定收藏**'), self.subscribe_playlist,
                current_item),
                    ]
            menu_items = [
                    (None, _('收藏歌单'), Menu(subscribe_submenu)),
                    ]
            Menu(menu_items, True).show((x, y))

    def subscribe_playlist(self, current_item):
        if nplayer.subscribe_playlist(current_item.get_playlist_id):
            event_manager.emit('refresh-online-lists')

    def clear_items(self):
        self.clear()

    def draw_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutMiddle")

class SearchSongItem(TreeItem):
    def __init__(self, song):

        TreeItem.__init__(self)

        self.song_error = False
        self.update(song)
        self.height = 26

        self.is_highlight = False
        self.column_index = 0

        self.default_height = 26

    def emit_redraw_request(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def update(self, song, redraw=False):
        '''update'''
        self.song = song
        self.title = song.get_str("name")
        self.artist = ','.join([artist['name'] for artist in
            song['artists']])
        self.album = song["album"]["name"]
        self.length = utils.duration_to_string(int(song.get_str("duration")))

        self.tooltip_text = "曲名：" + self.title + "\n歌手：" + self.artist + "\n时长：" + self.length + "\n专辑：" + self.album

        # Calculate item size.
        self.title_padding_x = 15
        self.title_padding_y = 5
        (self.title_width, self.title_height) = get_content_size(self.title, DEFAULT_FONT_SIZE)

        self.artist_padding_x = 10
        self.artist_padding_y = 5
        (self.artist_width, self.artist_height) = get_content_size(self.artist, DEFAULT_FONT_SIZE)

        self.length_padding_x = 2
        self.length_padding_y = 5
        (self.length_width, self.length_height) = get_content_size(self.length, DEFAULT_FONT_SIZE)

        if redraw:
            self.emit_redraw_request()

    def set_error(self):
        if not self.song_error:
            self.song_error = True
            self.emit_redraw_request()

    def clear_error(self):
        if self.song_error:
            self.song_error = False
            self.emit_redraw_request()

    def exists(self):
        return self.song.exists()

    def is_error(self):
        return self.song_error == True

    def render_title(self, cr, rect):
        '''Render title.'''
        if self.is_highlight:
            draw_single_mask(cr, rect.x + 1, rect.y, rect.width, rect.height, "globalItemHighlight")
        elif self.is_select:
            draw_single_mask(cr, rect.x + 1, rect.y, rect.width, rect.height, "globalItemSelect")
        elif self.is_hover:
            draw_single_mask(cr, rect.x + 1, rect.y, rect.width, rect.height, "globalItemHover")

        # if self.is_highlight:
        #     text_color = "#ffffff"
        # else:
        #     text_color = app_theme.get_color("labelText").get_color()

        rect.x += self.title_padding_x
        rect.width -= self.title_padding_x * 2
        render_item_text(cr, self.title, rect, self.is_select, self.is_highlight, error=self.song_error)

    def render_artist(self, cr, rect):
        '''Render artist.'''
        if self.is_highlight:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHighlight")
        elif self.is_select:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemSelect")
        elif self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")


        rect.x += self.artist_padding_x
        rect.width -= self.artist_padding_x * 2
        render_item_text(cr, self.artist, rect, self.is_select, self.is_highlight, error=self.song_error)

    def render_length(self, cr, rect):
        '''Render length.'''
        if self.is_highlight:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHighlight")
        elif self.is_select:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemSelect")
        elif self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")


        rect.width -= self.length_padding_x * 2
        rect.x += self.length_padding_x * 2
        render_item_text(cr, self.length, rect, self.is_select, self.is_highlight, error=self.song_error, font_size=8)

    def get_height(self):
        # if self.is_highlight:
        #     return 32
        return self.default_height

    def get_column_widths(self):
        '''Get sizes.'''
        return (156, 51, 102)

    def get_column_renders(self):
        '''Get render callbacks.'''

        return (self.render_title, self.render_length, self.render_artist)

    def unselect(self):
        self.is_select = False
        self.emit_redraw_request()

    def select(self):
        self.is_select = True
        self.emit_redraw_request()

    def highlight(self):
        self.is_highlight = True
        self.is_select = False
        self.emit_redraw_request()

    def unhighlight(self):
        self.is_highlight = False
        self.is_select = False
        self.emit_redraw_request()

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        self.emit_redraw_request()

    def hover(self, column, offset_x, offset_y):
        event_manager.emit("update-song-tooltip",
                HTMLParser().unescape(self.tooltip_text))
        self.is_hover = True
        self.emit_redraw_request()

    def get_song(self):
        return self.song

    def __hash__(self):
        return hash(self.song.get("uri"))

    def __repr__(self):
        return "<SearchSongItem %s>" % self.song.get("uri")

    def __cmp__(self, other_item):
        if not other_item:
            return -1
        try:
            return cmp(self.song, other_item.get_song())
        except AttributeError: return -1

    def __eq__(self, other_item):
        try:
            return self.song == other_item.get_song()
        except:
            return False

class SongView(TreeView):
    CREATED_LISTS_DICT = {}
    __gsignals__ = {
            "begin-add-items" :
                (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
            "empty-items" :
                (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
            }

    def __init__(self):
        TreeView.__init__(self, enable_drag_drop=False,
                enable_multiple_select=True)

        # view_type 为list类型
        self.connect("double-click-item", self.on_music_view_double_click)
        self.connect("press-return", self.on_music_view_press_return)
        self.connect("right-press-items", self.on_music_view_right_press_items)
        event_manager.connect("update-song-tooltip",
                self.update_song_tooltip)

        self.onlinelist_thread_id = 0

    @property
    def items(self):
        return self.get_items()

    def on_music_view_double_click(self, widget, item, column, x, y):
        if item:
            sid = item.get_song()['id']
            self.add_play_emit([sid])

    def on_music_view_press_return(self, widget, items):
        if items:
            sids = [item.get_song()['id'] for item in items]
            self.add_play_emit(sids)

    def add_play_emit(self, sids):
        songs = nplayer.songs_detail(sids)
        songs = [Song(song) for song in songs]
        event_manager.emit('add-songs-to-playing-list', (songs, True))

    def add_to_playlist(self, songs):
        self.add_and_play_songs = songs
        event_manager.emit('add-songs-to-playing-list')

    def on_music_view_right_press_items(self, widget, x, y,
            current_item, select_items):
        if current_item and select_items:
            selected_songs_id = [item.get_song()['id'] for item in select_items]
            # 子菜单 - 添加到创建的歌单
            addto_submenu = [(None, _(gobject.markup_escape_text(key)),
                self.add_to_list, selected_songs_id,
                self.CREATED_LISTS_DICT[key]) for key in self.CREATED_LISTS_DICT.keys()]
            addto_submenu.insert(0,(None, _('播放列表'),
                self.add_to_list, selected_songs_id, 0))
            addto_submenu = Menu(addto_submenu)

            if len(select_items) > 1:
                items = [
                        (None, _("播放"), lambda: self.add_play_emit(
                            [item.get_song()['id'] for item in select_items])),
                        ]
            else:
                items = [
                        (None, _("播放"), lambda:
                            self.add_play_emit([current_item.get_song()['id']])),
                        ]
            items.insert(0, (None, _("添加到"), addto_submenu))
            Menu(items, True).show((int(x), int(y)))

    def add_to_list(self, sids, playlist_id=0):
        if playlist_id and nplayer.add_to_onlinelist(sids, playlist_id):
            event_manager.emit('refresh-online-list', playlist_id)
        elif not playlist_id:
            event_manager.emit('add-songs-to-playing-list',
                    (nplayer.songs_detail(sids), False))

    def get_sids(self, items):
        return ",".join([str(item.song['sid']) for item in items if
            item.song.get('sid', None)])

    def update_song_tooltip(self, widget, text):
        self.set_tooltip_text(text)

    def clear_items(self):
        self.clear()
        event_manager.emit("save-playing-status")

    def draw_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutMiddle")

    # set self as current global playlist
    def set_current_source(self):
        if Player.get_source() != self:
            Player.set_source(self)

    def emit_add_signal(self):
        self.emit("begin-add-items")

    def get_songs(self):
        songs = []
        self.update_item_index()
        for song_item in self.items:
            songs.append(song_item.get_song())
        return songs

    def add_songs(self, songs, pos=None, sort=False, play=False):
        if not songs:
            return

        try:
            song_items = [ SearchSongItem(song) for song in songs if song not in
                    self.get_songs() ]
        except:
            song_items = [ SearchSongItem(Song(song)) for song in songs if song not in
                    self.get_songs() ]

        if song_items:
            if not self.items:
                self.emit_add_signal()
            self.add_items(song_items, pos, False)
            event_manager.emit("save-playing-status")

        if len(songs) >= 1 and play:
            song = songs[0]
            self.request_song(song, play=True)

    def set_highlight_song(self, song):
        if not song: return
        if SearchSongItem(song) in self.items:
            self.set_highlight_item(self.items[self.items.index(SearchSongItem(Song(song)))])
            self.visible_highlight()
            self.queue_draw()

    def update_songitem(self, song):
        if not song: return
        if song in self.items:
            self.items[self.items.index(SearchSongItem(song))].update(song, True)

    def dump_songs(self):
        return [ song.get_dict() for song in self.get_songs() ]

    @property
    def current_song(self):
        if self.highlight_item:
            return self.highlight_item.get_song()
        return None

class BaseWebView(WebView):
    def __init__(self, url, enable_plugins=False, cookie=get_cookie_file()):
        super(BaseWebView, self).__init__(cookie)

        # Init objects
        self._player = neteasecloud_music_player
        self._player_interface = player_interface
        #self._ttp_download = ttp_download

        class External(object):
            NeteaseCloudMusic = self._player

        self.external = External()

        # Disable webkit plugins
        settings = self.get_settings()
        settings.set_property('enable-plugins', enable_plugins)
        self.set_settings(settings)

        # Load URI
        if url:
            self.load_uri(url)

        # Javascriptcore context
        #self.js_context = jscore.JSContext(
                #self.get_main_frame().get_global_context()).globalObject
        #self._player.__class__.js_context = self.js_context

         #Set connect signal
        self.connect("window-object-cleared", self.on_webview_object_cleared)
        self.connect("script-alert", self.on_script_alert)
        self.connect("console-message", self.on_console_message)
        self.connect("resource-load-failed", self.on_resouse_load_failed)
        self.connect("load-progress-changed", self.on_webview_progress_changed)
        self.connect("load-finished", self.on_webview_load_finished)

    def on_webview_object_cleared(self, *args):
        self.injection_object()
        return True

    def on_script_alert(self, widget, frame, message):
        self.injection_object()
        self._player.alert(message)
        return True

    def on_console_message(self, widget, message, line, source_id):
        return True

    def on_resouse_load_failed(self, *args):
        self.injection_object()

    def injection_css(self):
        pass

    def injection_object(self):
        return
        self.injection_css()
        self.js_context.window.external = self.external
        self.js_context.player = self._player
        self.js_context.link_support = True
        self.js_context.mv_support = True
        self.js_context.pop_support = True

        #self.js_context.window.top.ttp_download = self._ttp_download
        self.js_context.window.top.playerInterface = self._player_interface
        self.js_context.alert = self._player.alert
        try:
            self.injection_frame_object()
        except:
            pass

    def injection_frame_object(self):
        return
        self.js_context.window.frames['centerFrame'].window.external \
                = self.external
        self.js_context.window.frames['centerFrame'].player \
                = self._player
        self.js_context.window.frames['centerFrame'].link_support \
                = True
        self.js_context.window.frames['centerFrame'].mv_support \
                = True
        self.js_context.window.frames['centerFrame'].pop_support \
                = True
        self.js_context.window.frames['centerFrame'].window.top.playerInterface\
                = self._player_interface
        self.js_context.window.frames['centerFrame'].alert\
                = self._player.alert
        #self.js_context.window.frames['centerFrame'].window.top.ttp_download\
                #= self._ttp_download

    def on_webview_load_finished(self, *args):
        self.injection_object()

    def on_webview_progress_changed(self, widget, value):
        self.injection_object()

class LoginDialog(DialogBox):
    def __init__(self, url=None):
        DialogBox.__init__(self, "登录", 600, 385, DIALOG_MASK_MULTIPLE_PAGE,
                close_callback=self.hide_all, modal=False,
                window_hint=None, skip_taskbar_hint=False,
                window_pos=gtk.WIN_POS_CENTER)

        #self.set_keep_above(True)
        #self.is_reload_flag = False
        self.webview = BaseWebView(url)
        self.webview.connect("notify::load-status",
                self.handle_login_dialog_status)
        webview_align = gtk.Alignment()
        webview_align.set(1, 1, 1, 1)
        webview_align.set_padding(0, 0, 0, 2)
        webview_align.add(self.webview)
        self.body_box.pack_start(webview_align, False, True)

    def handle_login_dialog_status(self, *kwargs):
        # When load finished
        if str(self.webview.get_load_status()) == "<enum WEBKIT_LOAD_FINISHED of type WebKitLoadStatus>":
            # Show current URL in terminal
            url = self.webview.get_property('uri')
            print "current url>>> ", url

            # Hide an element
            if 'https://api.weibo.com/oauth2/authorize' in url:
                self.webview.execute_script('document.getElementsByClassName("WB_btn_pass")[0].style.display="None"')

            elif 'http://music.163.com/back/weibo?error' in url:
                self.close()
            elif 'http://music.163.com/back/weibo?state=' in url:
                # load cookie
                cookie = {}
                with open(get_cookie_file(), 'r') as f:
                    for line in f.readlines():
                        if "music.163.com" in line:
                            line = line.split()
                            cookie[line[5]] = line[6]
                nplayer.cookies = cookie
                nplayer.save_uid_and_cookies()
                print 'login-success emit from LoginDialog'
                event_manager.emit("login-success")
                self.close()

    def draw_view_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutMiddle")
