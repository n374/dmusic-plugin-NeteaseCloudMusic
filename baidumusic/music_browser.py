#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
import javascriptcore as jscore
from dtk.ui.browser import WebView

from widget.ui import NetworkConnectFailed
from dtk.ui.dialog import DialogBox, DIALOG_MASK_MULTIPLE_PAGE

from deepin_utils.net import is_network_connected
from widget.ui_utils import switch_tab, draw_alpha_mask
from music_player import baidu_music_player, player_interface, ttp_download
from music_tools import get_cookie_file

from events import event_manager


class BaseWebView(WebView):
    
    def __init__(self, url, enable_plugins=False, cookie=get_cookie_file()):
        super(BaseWebView, self).__init__(cookie)
        
        # Init objects
        self._player = baidu_music_player
        self._player_interface = player_interface
        self._ttp_download = ttp_download
        
        class External(object):
            BaiduMusic = self._player
            BaiduMusic2 = self._player
            BaiduMusic3 = self._player
            BaiduMusic4 = self._player
            
        self.external = External()    
        
        # disable webkit plugins.
        settings = self.get_settings()
        settings.set_property('enable-plugins', enable_plugins)
        self.set_settings(settings)
        
        # load uri
        if url:
            self.load_uri(url)
            
        # javascriptcore context.
        self.js_context = jscore.JSContext(self.get_main_frame().get_global_context()).globalObject                                
        
        self._player.__class__.js_context = self.js_context
        
        # connect signals.
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
        
        # reject alert dialog.
        return True
    
    def on_console_message(self, widget, message, line, source_id):
        return True
    
    def on_resouse_load_failed(self, *args):    
        self.injection_object()
        
    def injection_css(self):    
        pass
        
    def injection_object(self):
        self.injection_css()
        self.js_context.window.external = self.external
        self.js_context.player = self._player
        self.js_context.link_support = True
        self.js_context.mv_support = True
        self.js_context.pop_support = True
        
        self.js_context.window.top.ttp_download = self._ttp_download
        self.js_context.window.top.playerInterface = self._player_interface
        self.js_context.alert = self._player.alert
        try:        
            self.injection_frame_object()
        except:    
            pass
        
    def injection_frame_object(self):
        self.js_context.window.frames['centerFrame'].window.external = self.external
        self.js_context.window.frames['centerFrame'].player = self._player
        self.js_context.window.frames['centerFrame'].link_support = True
        self.js_context.window.frames['centerFrame'].mv_support = True
        self.js_context.window.frames['centerFrame'].pop_support = True
        self.js_context.window.frames['centerFrame'].window.top.playerInterface = self._player_interface
        self.js_context.window.frames['centerFrame'].alert = self._player.alert
        self.js_context.window.frames['centerFrame'].window.top.ttp_download = self._ttp_download
        
    def on_webview_load_finished(self, *args):    
        # inject object.    
        self.injection_object()            
        
    def on_webview_progress_changed(self, widget, value):    
        self.injection_object()
        

class LoginDialog(DialogBox):
    
    def __init__(self):
        DialogBox.__init__(self, "登录", 326, 340, DIALOG_MASK_MULTIPLE_PAGE, 
                           close_callback=self.hide_all, modal=False,
                           window_hint=None, skip_taskbar_hint=False,
                           window_pos=gtk.WIN_POS_CENTER)
        
        self.set_keep_above(True)
        self.is_reload_flag = False
        self.webview = BaseWebView("http://musicmini.baidu.com/app/passport/passport_phoenix.html")
        webview_align = gtk.Alignment()
        webview_align.set(1, 1, 1, 1)
        webview_align.set_padding(0, 0, 0, 2)
        webview_align.add(self.webview)
        self.body_box.pack_start(webview_align, False, True)
        
    def draw_view_mask(self, cr, x, y, width, height):            
        draw_alpha_mask(cr, x, y, width, height, "layoutMiddle")
        
class MVBrowser(DialogBox):        
    def __init__(self):
        DialogBox.__init__(self, "登录", 645, 500, DIALOG_MASK_MULTIPLE_PAGE, 
                           close_callback=self.hide_all, modal=False,
                           window_hint=None, skip_taskbar_hint=False,
                           window_pos=gtk.WIN_POS_CENTER)
        
        self.url = "http://musicmini.baidu.com/app/mv/playMV.html"
        self.webview = BaseWebView("", enable_plugins=True)
        webview_align = gtk.Alignment()
        webview_align.set(1, 1, 1, 1)
        webview_align.set_padding(0, 0, 0, 2)
        webview_align.add(self.webview)
        self.body_box.pack_start(webview_align, False, True)
        
    def draw_view_mask(self, cr, x, y, width, height):            
        draw_alpha_mask(cr, x, y, width, height, "layoutMiddle")
        
    def play_mv(self):    
        self.webview.load_uri(self.url)
        self.show_window()
    

class MusicBrowser(gtk.VBox):
    
    def __init__(self):
        super(MusicBrowser, self).__init__()
        
        # check network status
        self.progress_value = 0
        self.is_reload_flag = False        
        self.network_connected_flag = False
        self.network_failed_box = NetworkConnectFailed(self.check_network_connection)


        self.webview = BaseWebView("http://musicmini.baidu.com/")
        self.js_context = self.webview.js_context        
        self.webview.injection_css = self.injection_css
        
        self.check_network_connection(auto=True)        
        
        self.login_dialog = LoginDialog()
        self.mv_window = MVBrowser()
        
        event_manager.connect("login-dialog-run", self.on_login_dialog_run)
        event_manager.connect("login-success", self.on_login_success)
        event_manager.connect("play-mv", self.on_play_mv)
        
    def on_play_mv(self, obj, data):    
        self.mv_window.play_mv()
        
    def on_login_dialog_run(self, obj, data):    
        self.login_dialog.show_window()
        
    def on_login_success(self, obj, data):    
        self.login_dialog.hide_all()

    def check_network_connection(self, auto=False):    
        if is_network_connected():
            self.network_connected_flag = True
            switch_tab(self, self.webview)
            if not auto:
                self.reload_browser()
        else:    
            self.network_connected_flag = False
            switch_tab(self, self.network_failed_box)
            
    def reload_browser(self):        
        self.is_reload_flag = False
        self.update_progress_flag = True
        self.progress_value = 0
        self.webview.reload()
        
    def injection_css(self):    
        try:
            self.js_context.window.frames['centerFrame'].document.querySelector('#mainDiv').style.height = "405px"
            self.js_context.document.getElementById("mainDiv").style.height = "405px"
        except: pass
