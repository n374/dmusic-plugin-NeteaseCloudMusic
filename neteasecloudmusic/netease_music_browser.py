#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
#import javascriptcore as jscore
from dtk.ui.browser import WebView

from widget.ui import NetworkConnectFailed
from dtk.ui.dialog import DialogBox, DIALOG_MASK_MULTIPLE_PAGE

from deepin_utils.net import is_network_connected
from widget.ui_utils import switch_tab, draw_alpha_mask
from netease_music_player import neteasecloud_music_player, player_interface
from netease_music_player import neteasecloud_music_player as nplayer
from netease_music_tools import get_cookie_file

from netease_events import event_manager

#from widget.completion_window import search_entry
#from widget.browser_manager import BrowserMananger
from player import Player
#from widget.global_search import GlobalSearch
#from dtk.ui.paned import HPaned
from widget.skin import app_theme
from netease_music_view import CategoryView, MusicView
from dtk.ui.treeview import TreeItem
from widget.ui_utils import (draw_single_mask, switch_tab,
                             draw_alpha_mask, render_item_text)
from dtk.ui.draw import draw_text
from widget.song_item import SongItem
from dtk.ui.utils import get_content_size
from song import Song
import pango
DEFAULT_FONT_SIZE = 8
class MusicBrowser(gtk.VBox):
    def __init__(self):
        super(MusicBrowser, self).__init__(False)
        self.search_box = gtk.HBox(False)
        #self.search_box.set_size_request(400, -1)
        self.result_box = gtk.HBox(False)

        self.search_entry = gtk.Entry()
        self.search_entry.set_width_chars(62)
        self.search_entry.connect('activate', self.search)
        self.search_button = gtk.Button("Search")
        self.search_button.connect('pressed', self.search)

        self.song_list = CategoryView(enable_drag_drop=False,
                enable_multiple_select=True)
        self.playlist_list = CategoryView(enable_drag_drop=False,
                enable_multiple_select=True)

        self.playlist_list.connect('single-click-item', self.single_click_item)
        self.playlist_list.connect('right-press-items', self.right_click_item)

        self.search_box.pack_start(self.search_entry, False, False)
        self.search_box.pack_end(self.search_button, False, False)
        self.result_box.pack_start(self.playlist_list)
        self.result_box.pack_end(self.song_list)
        self.pack_start(self.search_box, False, False, 0)
        self.pack_end(self.result_box)
        self.show_all()
        self.playlist_list.add_items([PlaylistItem(playlist) for playlist in
            nplayer.search('你好', 1000)], clear_first=True)
        self.song_list.add_items([SongItem(Song(song)) for song in
            nplayer.search('你好')], clear_first=True)

    def search(self, *kwargs):
        string = self.search_entry.get_text()
        if string:
            self.playlist_list.add_items([PlaylistItem(playlist) for playlist in
                nplayer.search(string, 1000)], clear_first=True)
            self.song_list.add_items([SongItem(Song(song)) for song in
                nplayer.search(string)], clear_first=True)

    def single_click_item(self, widget, item, column, x, y):
        """ Switch view_box content when click category_list's item """
        print item.get_playlist['name'], item.get_playlist['id']

    def right_click_item(self, widget, x, y, item, column):
        print item.get_playlist['name'], item.get_playlist['id']

class PlaylistItem(TreeItem):
    def __init__(self, data):
        TreeItem.__init__(self)

        self.update(data, True)
        self.column_index = 0
        self.side_padding = 5
        self.is_highlight = False
        self.padding_y = 0
        self.padding_x = 8
        self.item_height = 20
        self.item_width = 90

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

    def get_height(self):
        return self.item_height

    def get_column_widths(self):
        return (self.item_width,)

    def get_column_renders(self):
        return (self.render_title,)

    def emit_redraw_request(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def set_title(self, title):
        self.title = title
        self.emit_redraw_request()

    def render_title(self, cr, rect):
        # Draw select background.

        rect.y += self.padding_y + 2
        # draw separator
        if self.is_highlight:
            draw_single_mask(cr, rect.x+1, rect.y, rect.width-2, rect.height,
                    "globalItemHighlight")
        elif self.is_hover:
            draw_single_mask(cr, rect.x+1, rect.y, rect.width-2, rect.height,
                    "globalItemHover")

        rect.x += self.padding_x
        rect.width -= self.padding_x * 2

        if self.is_highlight:
            text_color = "#FFFFFF"
        else:
            text_color = app_theme.get_color("labelText").get_color()

        draw_text(cr, self.title, rect.x, rect.y, rect.width, rect.height,
            text_size=10, text_color=text_color, alignment=pango.ALIGN_LEFT)

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

    @property
    def list_widget(self):
        switch_tab(self.main_box, self.song_view)
        if not nplayer.is_login and self.list_type == MusicView.LOGIN_LIST_TYPE:
            switch_tab(self.main_box, self.login_box)

        return self.main_box

    def dump_list(self):
        songs = self.song_view.dump_songs()
        return (self.title, songs)

    get_playlist = property(lambda self: self.playlist)
    #add_songs = property(lambda self: self.song_view.add_songs)
    #refrush = property(lambda self: self.song_view.refrush)
    playlist_id = property(lambda self: self.list_id)
    #current_song = property(lambda self: self.song_view.current_song)
    #play_song = property(lambda self: self.song_view.request_song)

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
                nplayer.save_cookie(cookie)
                print 'login-success emit from LoginDialog'
                event_manager.emit("login-success")
                self.close()

    def draw_view_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutMiddle")
