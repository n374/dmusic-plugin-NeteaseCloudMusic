#! /usr/bin/env python
# -*- coding: utf-8 -*-

import dtk.ui.tooltip as Tooltip
from dtk.ui.button import ImageButton, ToggleButton
from widget.skin import app_theme

def create_toggle_button(name, callback=None, tip_msg=None, parent=False):        
    toggle_button = ToggleButton(
        app_theme.get_pixbuf("%s_normal.png" % name),
        app_theme.get_pixbuf("%s_press.png" % name),
        )
    
    if callback:
        toggle_button.connect("toggled", callback)
        
    if tip_msg:
        Tooltip.text(toggle_button, tip_msg)
        
    if parent:    
        parent.pack_start(toggle_button, False, False)
    return toggle_button


def create_button(name, callback=None, tip_msg=None, parent=None, no_hover=False):        
    hover = "press" if no_hover else "hover"
    button = ImageButton(
        app_theme.get_pixbuf("%s_normal.png" % name),
        app_theme.get_pixbuf("%s_%s.png" % (name, hover)),
        app_theme.get_pixbuf("%s_press.png" % name),
        )
    if callback:
        button.connect("button-press-event", callback)
    if tip_msg:
        Tooltip.text(button, tip_msg)
        
    if parent:    
        parent.pack_start(button, False, False)
    return button

