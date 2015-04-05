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

class RadioItem(TreeItem):
    
    def __init__(self, data):
        super(RadioItem, self).__init__()
        
        self.column_index = 0
        self.is_highlight = False
        self.normal_height = 54
        self.item_width = CATEGROYLIST_WIDTH
        
    def get_height(self):    
        return self.normal_height
    
    def get_column_widths(self):
        return (self.item_width,)
    
    def get_column_renders(self):
        return (self.render_content,)
    
    def emit_redraw_request(self):    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def render_content(self, cr, rect):        
        pass
    
