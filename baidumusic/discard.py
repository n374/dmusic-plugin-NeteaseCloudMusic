#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
import javascriptcore as jscore
from dtk.ui.browser import WebView

from widget.ui import NetworkConnectFailed, LoadingBox
from dtk.ui.dialog import DialogBox, DIALOG_MASK_MULTIPLE_PAGE

from deepin_utils.net import is_network_connected
from widget.ui_utils import switch_tab, draw_alpha_mask
from music_player import baidu_music_player, player_interface, ttp_download
from music_tools import get_cookie_file

from events import event_manager


class BaseWebView(WebView):
    
    def __init__(self, url, cookie=get_cookie_file()):
        super(BaseWebView, self).__init__(cookie)
        
        # Init objects
        self._player = baidu_music_player
        self._player_interface = player_interface
        self._ttp_download = ttp_download
        
        # disable webkit plugins.
        settings = self.get_settings()
        settings.set_property('enable-plugins', False)
        self.set_settings(settings)
        
        # load uri
        if url:
            self.load_uri(url)
            
        # javascriptcore context.
        self.js_context = jscore.JSContext(self.get_main_frame().get_global_context()).globalObject                                
        
        self._player.__class__.js_context = self.js_context
        
        # connect signals.
        self.connect("script-alert", self.on_script_alert)        
        self.connect("console-message", self.on_console_message)
        self.connect("resource-load-failed", self.on_resouse_load_failed)
        
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
        self.js_context.player = self._player
        self.js_context.window.top.ttp_download = self._ttp_download
        self.js_context.window.top.playerInterface = self._player_interface
        self.js_context.link_support = True
        self.js_context.alert = self._player.alert
        

class LoginDialog(DialogBox):
    
    def __init__(self):
        DialogBox.__init__(self, "登录", 326, 340, DIALOG_MASK_MULTIPLE_PAGE, 
                           close_callback=self.hide_all, modal=False,
                           window_hint=None, skip_taskbar_hint=False,
                           window_pos=gtk.WIN_POS_CENTER)
        
        self.set_keep_above(True)
        self.is_reload_flag = False
        self.webview = BaseWebView("http://musicmini.baidu.com/app/passport/passport_phoenix.html")
        self.webview.connect("load-finished", self.on_webview_load_finished)
        webview_align = gtk.Alignment()
        webview_align.set(1, 1, 1, 1)
        webview_align.set_padding(0, 0, 0, 2)
        webview_align.add(self.webview)
        self.body_box.pack_start(webview_align, False, True)
        
    def draw_view_mask(self, cr, x, y, width, height):            
        draw_alpha_mask(cr, x, y, width, height, "layoutMiddle")
        
    def on_webview_load_finished(self, *args):    
        if not self.is_reload_flag:
            self.webview.reload()
            self.is_reload_flag = True
        self.webview.injection_object()
        

class MusicBrowser(gtk.VBox):
    
    def __init__(self):
        super(MusicBrowser, self).__init__()
        
        # check network status
        self.progress_value = 0
        self.is_reload_flag = False        
        self.network_connected_flag = False
        self.update_progress_flag = True
        self.prompt_text = "正在加载数据(%d%%)，如果长时间没有响应，点击此处刷新"
        self.loading_box = LoadingBox(self.prompt_text % self.progress_value, "此处", self.reload_browser)
        self.network_failed_box = NetworkConnectFailed(self.check_network_connection)
        self.check_network_connection(auto=True)

        self.webview = BaseWebView("http://musicmini.baidu.com/static/recommend/recommend.html")
        self.js_context = self.webview.js_context        
        self.webview.injection_css = self.injection_css
        self.webview.connect("load-progress-changed", self.on_webview_progress_changed)        
        self.webview.connect("load-finished", self.on_webview_load_finished)        
        
        self.login_dialog = LoginDialog()
        event_manager.connect("login-dialog-run", self.on_login_dialog_run)
        event_manager.connect("login-success", self.on_login_success)
        
    def on_login_dialog_run(self, obj, data):    
        self.login_dialog.show_window()
        
    def on_login_success(self, obj, data):    
        self.login_dialog.hide_all()

    def on_webview_progress_changed(self, widget, value):    
        if self.update_progress_flag:
            if self.is_reload_flag:
                self.progress_value = (100 + value ) / 200.0
            else:    
                self.progress_value = value / 200.0            
                
            self.loading_box.update_prompt_text(self.prompt_text % int(self.progress_value * 100))    
        
    def check_network_connection(self, auto=False):    
        if is_network_connected():
            self.network_connected_flag = True
            switch_tab(self, self.loading_box)
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
            main_div = self.js_context.document.getElementById("mainDiv")
            main_div.style.height = "405px"            
        except: pass
        
    def on_webview_load_finished(self, *args):    
        if not self.is_reload_flag:
            self.webview.reload()
            self.is_reload_flag = True
        elif self.is_reload_flag and self.update_progress_flag:    
            self.update_progress_flag = False
            if self.network_connected_flag:
                switch_tab(self, self.webview)
            
        # inject object.    
        self.webview.injection_object()            
