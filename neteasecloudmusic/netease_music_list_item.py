#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pango
import gtk
from dtk.ui.draw import draw_pixbuf, draw_text
from dtk.ui.treeview import TreeItem

from widget.skin import app_theme
from widget.ui_utils import (draw_single_mask, draw_separator, switch_tab,
                             create_left_align, create_right_align,
                             create_upper_align, create_bottom_align,
                             draw_alpha_mask)

import utils
from widget.ui import ComplexButton
from constant import PLAYLIST_WIDTH, CATEGROYLIST_WIDTH
from netease_music_view import MusicView, nplayer
from netease_music_tools import get_image
from netease_events import event_manager

class LoginButton(ComplexButton):
    def __init__(self, callback=None):
        bg_group = (app_theme.get_pixbuf("jobs/complex_normal.png"),
                    app_theme.get_pixbuf("jobs/complex_hover.png"),
                    app_theme.get_pixbuf("jobs/complex_press.png"))

        icon = app_theme.get_pixbuf("filter/artist_normal.png")
        super(LoginButton, self).__init__(bg_group, icon, "登录网易账号",
                left_padding=10)

        if callback:
            self.connect("clicked", callback)

class LoginBox(gtk.HBox):
    def __init__(self, callback=None):
        super(LoginBox, self).__init__()

        self.login_button = LoginButton(callback)
        self.username_entry = gtk.Entry()
        self.username_entry.set_text('username')
        self.password_entry = gtk.Entry()
        self.password_entry.set_text('password')
        self.password_entry.set_visibility(False)
        content_box = gtk.VBox()
        content_box.pack_start(create_bottom_align(), True, True)
        content_box.pack_start(self.username_entry, False, False)
        content_box.pack_start(self.password_entry, False, False)
        login_box = gtk.HButtonBox()
        login_box.pack_start(self.login_button, False, False, 16)
        content_box.pack_start(login_box, False, False, 16)
        content_box.pack_start(create_upper_align(), True, True)

        self.pack_start(create_right_align(), True, True)
        self.pack_start(content_box, False, False)
        self.pack_start(create_left_align(), True, True)
        self.set_size_request(PLAYLIST_WIDTH, -1)
        self.connect("expose-event", self.on_loginbox_expose)

    def on_loginbox_expose(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        draw_alpha_mask(cr, rect.x, rect.y,
                rect.width, rect.height, "layoutMiddle")

class MusicListItem(TreeItem):
    PLAYING_LIST_TYPE = 1
    FAVORITE_LIST_TYPE = 2
    CREATED_LIST_TYPE = 3
    COLLECTED_LIST_TYPE = 4
    LOGIN_LIST_TYPE = 5
    PERSONAL_FM_ITEM = 6

    def __init__(self, list_data, list_type, is_online_list=False,
            has_separator=True):
        TreeItem.__init__(self)

        self.column_index = 0
        self.side_padding = 5
        self.is_highlight = False
        self.padding_y = 0
        self.padding_x = 8

        if list_type and list_type in [self.PLAYING_LIST_TYPE,
                self.PERSONAL_FM_ITEM, self.LOGIN_LIST_TYPE]:
            self.title = list_data
        else:
            self.title = list_data.get("name", "")
        self.data = list_data
        self.list_type= list_type

        if is_online_list:
            if self.data['specialType'] == 5:
                self.list_type = self.FAVORITE_LIST_TYPE
            elif self.data['subscribed']:
                self.list_type = self.COLLECTED_LIST_TYPE
            else:
                self.list_type = self.CREATED_LIST_TYPE

        self.has_separator = has_separator
        self.separator_height = 4
        self.item_width = CATEGROYLIST_WIDTH
        self.item_height = 26 + self.separator_height if self.has_separator else 26
        self.init_pixbufs()

        self.song_view = MusicView(data=self.data, view_type=self.list_type)
        self.song_view.set_size_request(PLAYLIST_WIDTH, -1)

        if self.list_type == self.LOGIN_LIST_TYPE:
            self.login_box = LoginBox(lambda w:
                    event_manager.emit("login"))

            event_manager.connect("login", self.login)

        self.main_box = gtk.VBox()

    def login(self, args=None, *kwargs):
        username = self.login_box.username_entry.get_text()
        password = self.login_box.password_entry.get_text()
        utils.ThreadFetch(
            fetch_funcs=(nplayer.login_and_get_cookie, (username,password)),
            success_funcs=(self.login_success, ())).start()

    def login_success(self, args, *kwargs):
        event_manager.emit('login-success')

    def init_pixbufs(self):
        if self.list_type == self.PLAYING_LIST_TYPE:
            normal_image_name = "playing_list.png"
            press_image_name = "playing_list_press.png"

        elif self.list_type == self.PERSONAL_FM_ITEM:
            normal_image_name = "personal_fm.png"
            press_image_name = "personal_fm_press.png"

        elif self.list_type == self.FAVORITE_LIST_TYPE:
            normal_image_name = "favorite_list.png"
            press_image_name = "favorite_list_press.png"

        elif self.list_type == self.CREATED_LIST_TYPE:
            normal_image_name = "created_list.png"
            press_image_name = "created_list_press.png"

        elif self.list_type == self.COLLECTED_LIST_TYPE:
            normal_image_name = "collected_list.png"
            press_image_name = "collected_list_press.png"
        else:
            normal_image_name = "marvin.png"
            press_image_name = "marvin.png"

        self.normal_pixbuf = gtk.gdk.pixbuf_new_from_file(
                                            get_image(normal_image_name))
        self.press_pixbuf = gtk.gdk.pixbuf_new_from_file(
                                            get_image(press_image_name))
        self.icon_width = self.normal_pixbuf.get_width()

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
        if self.has_separator:
            draw_separator(cr, rect.x, rect.y, rect.width, 1)
            rect.y += self.padding_y + self.separator_height - 2
            rect.height -= self.separator_height

        if self.is_highlight:
            draw_single_mask(cr, rect.x+1, rect.y, rect.width-2, rect.height,
                    "globalItemHighlight")
        elif self.is_hover:
            draw_single_mask(cr, rect.x+1, rect.y, rect.width-2, rect.height,
                    "globalItemHover")

        rect.x += self.padding_x
        rect.width -= self.padding_x * 2

        if self.is_highlight:
            pixbuf = self.press_pixbuf
        else:
            pixbuf = self.normal_pixbuf

        if pixbuf:
            icon_y = rect.y + (rect.height - self.normal_pixbuf.get_height())/2

            draw_pixbuf(cr, pixbuf, rect.x, icon_y)
            rect.x += self.icon_width + self.padding_x
            rect.width -= self.icon_width - self.padding_x

        if self.is_highlight:
            text_color = "#FFFFFF"
        else:
            text_color = app_theme.get_color("labelText").get_color()

        draw_text(cr, self.title, rect.x, rect.y, rect.width, rect.height,
            text_size=10, text_color=text_color, alignment=pango.ALIGN_LEFT)

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

    def on_event_login_success(self, obj, data):
        self.song_view.load_online_playlists(clear=True)
        switch_tab(self.main_box, self.song_view)

        self.emit_redraw_request()

    def dump_list(self):
        songs = self.song_view.dump_songs()
        return (self.title, songs)

    get_songs = property(lambda self: self.song_view.get_songs)
    add_songs = property(lambda self: self.song_view.add_songs)
    refrush = property(lambda self: self.song_view.refrush)
    list_id = property(lambda self: self.song_view.list_id)
    current_song = property(lambda self: self.song_view.current_song)
    play_song = property(lambda self: self.song_view.play_song)
