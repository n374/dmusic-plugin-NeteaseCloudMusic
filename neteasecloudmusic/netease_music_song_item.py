#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pango
from dtk.ui.utils import get_content_size
from dtk.ui.treeview import TreeItem
from widget.ui_utils import render_item_text, draw_single_mask
from HTMLParser import HTMLParser

from netease_music_song import Song
from netease_events import event_manager

DEFAULT_FONT_SIZE = 8

class SongItem(TreeItem):
    def __init__(self, song, extend=False):
        TreeItem.__init__(self)

        self.song_error = False
        self.update(song)
        self.extend = extend
        self.height = 26

        self.is_highlight = False
        self.column_index = 0

        self.default_height = 26

    def emit_redraw_request(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def update(self, song, redraw=False):
        '''update'''
        if not isinstance(song, Song):
            song = Song(song)
        self.song = song

        self.tooltip_text = ("曲名：" + self.song.song_name + "\n歌手："
                        + self.song.artist_names + "\n时长："
                        + str(self.song.length)
                        + "\n专辑：" + self.song.album_name)

        # Calculate item size.
        self.title_padding_x = 15
        self.title_padding_y = 5
        (self.title_width, self.title_height) = \
                get_content_size(self.song.song_name, DEFAULT_FONT_SIZE)

        self.artist_padding_x = 10
        self.artist_padding_y = 5
        (self.artist_width, self.artist_height) = \
                get_content_size(self.song.artist_names, DEFAULT_FONT_SIZE)

        self.length_padding_x = 2
        self.length_padding_y = 5
        (self.length_width, self.length_height) = \
                get_content_size(str(self.song.length), DEFAULT_FONT_SIZE)

        self.album_padding_x = 10
        self.album_padding_y = 5
        (self.album_width, self.album_height) = \
                get_content_size(self.song.album_name, DEFAULT_FONT_SIZE)

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
        render_item_text(cr, self.song.song_name, rect, self.is_select, self.is_highlight, error=self.song_error)

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
        render_item_text(cr, self.song.artist_names, rect, self.is_select,
                self.is_highlight, error=self.song_error,
                align=pango.ALIGN_RIGHT)

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
        render_item_text(cr, self.song.length, rect, self.is_select, self.is_highlight, error=self.song_error, font_size=8)

    def render_album(self, cr, rect):
        '''Render album.'''
        if self.is_highlight:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHighlight")
        elif self.is_select:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemSelect")
        elif self.is_hover:
            draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")

        rect.width -= self.album_padding_x * 2
        render_item_text(cr, self.song.album_name, rect, self.is_select, self.is_highlight, error=self.song_error)

    def get_height(self):
        # if self.is_highlight:
        #     return 32
        return self.default_height

    def get_column_widths(self):
        '''Get sizes.'''
        if self.extend:
            return (100, 100, 100, 90)
        else:
            return (156, 51, 102)


    def get_column_renders(self):
        '''Get render callbacks.'''

        if self.extend:
            return (self.render_title, self.render_artist, self.render_album, self.render_add_time)
        else:
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
        return hash(self.song.song_id)

    def __repr__(self):
        return "<SongItem %s>" % self.song.song_name

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
