#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pango
import gtk
from dtk.ui.draw import draw_pixbuf, draw_text
from dtk.ui.treeview import TreeItem

from widget.skin import app_theme
from widget.ui_utils import (draw_single_mask, draw_separator, switch_tab,
                             create_left_align, create_right_align,
                             create_upper_align, create_bottom_align, draw_alpha_mask)

from widget.ui import ComplexButton
from constant import PLAYLIST_WIDTH, CATEGROYLIST_WIDTH
from music_view import MusicView, bplayer
from music_tools import get_image
from events import event_manager

class LoginButton(ComplexButton):
    def __init__(self, callback=None):    
        bg_group = (app_theme.get_pixbuf("jobs/complex_normal.png"),
                    app_theme.get_pixbuf("jobs/complex_hover.png"),
                    app_theme.get_pixbuf("jobs/complex_press.png"))
        
        icon = app_theme.get_pixbuf("filter/artist_normal.png")
        super(LoginButton, self).__init__(bg_group, icon, "登录百度帐号", left_padding=10)
        
        if callback:
            self.connect("clicked", callback)
            
class LoginBox(gtk.HBox):            
        
    def __init__(self, callback=None):
        super(LoginBox, self).__init__()
        
        self.login_button = LoginButton(callback)
        content_box = gtk.VBox()
        content_box.pack_start(create_bottom_align(), True, True)
        content_box.pack_start(self.login_button, False, False)
        content_box.pack_start(create_upper_align(), True, True)
        
        self.pack_start(create_right_align(), True, True)
        self.pack_start(content_box, False, False)
        self.pack_start(create_left_align(), True, True)    
        self.set_size_request(PLAYLIST_WIDTH, -1)
        self.connect("expose-event", self.on_loginbox_expose)
        
    def on_loginbox_expose(self, widget, event):    
        cr = widget.window.cairo_create()
        rect = widget.allocation
        draw_alpha_mask(cr, rect.x, rect.y, rect.width, rect.height, "layoutMiddle")
        
class MusicListItem(TreeItem):    
    
    DEFAULT_TYPE = 1
    LOCAL_TYPE = 2    
    COLLECT_TYPE = 3
    PLAYLIST_TYPE = 4
    RADIO_TYPE = 5
    
    def __init__(self, data_or_title, list_type, has_separator=False):
        TreeItem.__init__(self)
        
        self.column_index = 0
        self.side_padding = 5
        self.is_highlight = False        
        self.padding_y = 0
        self.padding_x = 8
        self.list_type = list_type        
        
        if isinstance(data_or_title, basestring):
            self.title = data_or_title
            self.data = dict()
        else:    
            self.title = data_or_title.get("title", "")
            self.data = data_or_title
            
        self.data = data_or_title
        self.has_separator = has_separator        
        self.separator_height = 4
        self.item_width = CATEGROYLIST_WIDTH
        self.item_height = 26 + self.separator_height if has_separator else 26
        self.init_pixbufs()

        self.song_view = MusicView(view_type=list_type, data=self.data)
        # self.song_view.connect("begin-add-items", self.on_songview_begin_add_items)
        # self.song_view.connect("empty-items", self.on_songview_empty_items)
        self.song_view.set_size_request(PLAYLIST_WIDTH, -1)
        
        event_manager.connect("login-success", self.on_event_login_success)
        
        self.login_box = LoginBox(lambda w: event_manager.emit("login-dialog-run"))
        self.main_box = gtk.VBox()
        
    def on_songview_begin_add_items(self, widget):    
        pass
    
    def on_songview_empty_items(self, widget):
        pass
        
    def init_pixbufs(self):        
        if self.list_type == self.DEFAULT_TYPE:
            normal_image_name = "listen_list.png"
            press_image_name = "listen_list_press.png"
            
        elif self.list_type == self.LOCAL_TYPE:    
            normal_image_name = "local_list.png"
            press_image_name = "local_list_press.png"
            
        elif self.list_type == self.COLLECT_TYPE:    
            if bplayer.is_login:
                normal_image_name = "collect_list.png"
            else:    
                normal_image_name = "collect_list_unlogin.png"
            press_image_name = "collect_list_press.png"    
        else:    
            normal_image_name = "online_list.png"
            press_image_name = "online_list_press.png"
            
        self.normal_pixbuf = gtk.gdk.pixbuf_new_from_file(get_image(normal_image_name))
        self.press_pixbuf = gtk.gdk.pixbuf_new_from_file(get_image(press_image_name))
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
        # draw separator.
        if self.has_separator:
            draw_separator(cr, rect.x, 
                           rect.y,
                           rect.width, 1
                           )
            rect.y += self.padding_y + self.separator_height - 2
            rect.height -= self.separator_height
                    
        if self.is_highlight:    
            draw_single_mask(cr, rect.x + 1, rect.y, rect.width - 2, rect.height, "globalItemHighlight")
        elif self.is_hover:
            draw_single_mask(cr, rect.x + 1, rect.y, rect.width - 2, rect.height, "globalItemHover")
        
        rect.x += self.padding_x    
        rect.width -= self.padding_x * 2
            
        if self.is_highlight:
            pixbuf = self.press_pixbuf
        else:    
            pixbuf = self.normal_pixbuf
            
        if pixbuf:    
            icon_y = rect.y + (rect.height - self.normal_pixbuf.get_height()) / 2
            draw_pixbuf(cr, pixbuf, rect.x, icon_y)    
            rect.x += self.icon_width + self.padding_x
            rect.width -= self.icon_width - self.padding_x
            
        if self.is_highlight:
            text_color = "#FFFFFF"
        else:    
            text_color = app_theme.get_color("labelText").get_color()
            
        
        draw_text(cr, self.title, rect.x,
                  rect.y, rect.width,
                  rect.height, text_size=10, 
                  text_color = text_color,
                  alignment=pango.ALIGN_LEFT)    
        
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
        if self.list_type == self.DEFAULT_TYPE:
            pass

        elif self.list_type == self.COLLECT_TYPE:    
            if not bplayer.is_login:
                switch_tab(self.main_box, self.login_box)            
                
        return self.main_box
    
    def on_event_login_success(self, obj, data):
        if self.list_type == self.COLLECT_TYPE:
            self.song_view.load_collect_songs(clear=True)
            switch_tab(self.main_box, self.song_view)
            
            self.normal_pixbuf = gtk.gdk.pixbuf_new_from_file(get_image("collect_list.png"))
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
