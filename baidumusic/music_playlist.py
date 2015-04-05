#! /usr/bin/env python
# -*- coding: utf-8 -*-

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
from song import Song
from player import Player

from events import event_manager
from music_list_item import MusicListItem, bplayer
from music_view import CategoryView

def login_required(func):
    def inner(*args, **kwargs):
        if bplayer.is_login:
            return func(*args, **kwargs)
        else:
            event_manager.emit("login-dialog-run")
    return inner        


class MusicPlaylist(gtk.VBox):
    
    def __init__(self):
        super(MusicPlaylist, self).__init__()
        
        self.listen_db_file = get_cache_file("baidumusic/local_listen.db")
        self.status_db_file = get_cache_file("baidumusic/status.db")
        
        # Init default items        
        self.default_list_item = MusicListItem("试听列表", 
                                               list_type=MusicListItem.DEFAULT_TYPE)
        self.collect_list_item = MusicListItem("我的收藏", 
                                               list_type=MusicListItem.COLLECT_TYPE, 
                                               has_separator=True)
        
        # Init category list.
        self.category_list = CategoryView(enable_drag_drop=False, enable_multiple_select=True)
        self.category_list.add_items([self.default_list_item, self.collect_list_item])
        
        del self.category_list.keymap["Delete"]
        self.category_list.draw_mask = self.draw_category_list_mask
        self.category_list.set_size_request(CATEGROYLIST_WIDTH, -1)
        self.category_list.connect("single-click-item", self.on_category_single_click)
        self.category_list.connect("right-press-items", self.on_category_right_press)
        self.category_list.set_highlight_item(self.default_list_item)
        
        # View box
        self.view_box = gtk.VBox()
        self.view_box.connect("size-allocate", self.on_viewbox_size_allocate)
        self.view_box.add(self.default_list_item.list_widget)
        
        # bottom_box = gtk.HBox(spacing=45)
        # bottom_box_align = gtk.Alignment()
        # bottom_box_align.set(0.5, 0.5, 1, 1)
        # bottom_box_align.set_padding(2, 2, 28, 0)
        # bottom_box_align.set_size_request(-1, 22)
        # bottom_box_align.add(bottom_box)
        # bottom_box_align.connect("expose_event", self.on_bottombox_expose_event)
        # self.search_button = create_toggle_button("toolbar/search", parent=bottom_box)
        # self.person_button = create_button("combo/artist", parent=bottom_box, no_hover=True)
        
        main_paned = HPaned(handle_color=app_theme.get_color("panedHandler"), enable_drag=True)
        main_paned.pack1(self.category_list, True, True)
        main_paned.pack2(self.view_box, True, False)
        
        # events
        event_manager.connect("login-success", self.on_event_login_success)
        event_manager.connect("collect-songs", self.on_event_collect_songs)
        event_manager.connect("add-songs", self.on_event_add_songs)
        event_manager.connect("play-songs", self.on_event_play_songs)
        event_manager.connect("save-listen-lists", self.on_event_save_listen_lists)
        event_manager.connect("save-playlist-status", self.save_status)
        
        # load playlists.
        self.online_thread_id = 0
        self.new_list_thread_id = 0
        
        self.load()
        self.load_online_lists()
        self.load_status()
        
        self.add(main_paned)
        
    # access category_list highlight_item.    
    current_item = property(lambda self: self.category_list.highlight_item)    
    items = property(lambda self: self.category_list.visible_items)
    
    
    def load_status(self):
        obj = utils.load_db(self.status_db_file)
        if obj:
            index, d = obj
            song = Song()
            song.init_from_dict(d, cmp_key="sid")
        else:    
            index = 0
            song = None
            
        self.playlist_index = index
        self.last_song = song
    
    def save_status(self, *args):
        index = 0
        player_source = Player.get_source()
        for i, item in enumerate(self.category_list.get_items()):
            if item.song_view == player_source:
                index = i
                
        try:        
            song = self.current_item.current_song        
            utils.save_db((index, song.get_dict()), self.status_db_file)        
        except:    
            pass
    
    def restore_status(self):
        try:
            target_item = self.items[self.playlist_index]
        except:    
            target_item = None
            
        if target_item:    
            self.switch_view(target_item)
            if is_network_connected():
                self.current_item.play_song(self.last_song, play=True)
                    
    def draw_category_list_mask(self, cr, x, y, width, height):
        draw_alpha_mask(cr, x, y, width, height, "layoutLeft")
        
    def on_category_single_click(self, widget, item, cloumn, x, y):    
        ''' Switch view_box content when click category_list's item '''
        
        if item:
            self.switch_view(item)
    
    def on_category_right_press(self, widget, x, y, item, cloumn):
        menu_items = [
            (None, "新建试听列表", self.new_listen_list),
            (None, "新建在线歌单", self.new_online_list),
            ]
                
        if not item:
            Menu(menu_items, True).show((x, y))    
            return

        if item.list_type == MusicListItem.COLLECT_TYPE:
            if bplayer.is_login:
                menu_items = [
                    (None, "刷新", item.refrush),
                    (None, "新建歌单", self.new_online_list),
                    ]
            else:    
                menu_items = None
                
        elif item.list_type == MusicListItem.PLAYLIST_TYPE:    
            menu_items = [
                (None, "新建歌单", self.new_online_list),
                (None, "删除歌单", lambda : self.del_online_list(item)),
                (None, "重命名", lambda : self.rename_online_list(item)),
                (None, "刷新", item.refrush),
                ]
        elif item.list_type == MusicListItem.LOCAL_TYPE:    
            menu_items.extend([
                    (None, "删除列表", lambda : self.del_listen_list(item)),
                    (None, "重命名", lambda : self.rename_online_list(item, is_online=False))
                    ])
            
        if menu_items:    
            Menu(menu_items, True).show((x, y))
            
    def on_bottombox_expose_event(self, widget, event):        
        cr = widget.window.cairo_create()
        rect = widget.allocation
        cr.set_source_rgba(1, 1, 1, 0.95)
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
        
        draw_line(cr, (rect.x, rect.y + 1), 
                  (rect.x + rect.width, rect.y + 1), "#b0b0b0")
        return False
        
                
    def switch_view(self, item):
        ''' switch view_box's content '''
        
        self.category_list.set_highlight_item(item)
        switch_tab(self.view_box, item.list_widget)
    
    def save(self):
        local_lists = filter(lambda item: item.list_type == MusicListItem.LOCAL_TYPE, 
                             self.items)
        if len(local_lists) > 0:
            objs = [item.dump_list() for item in local_lists]
            utils.save_db(objs, self.listen_db_file)
    
    def load(self):
        objs = utils.load_db(self.listen_db_file)
        if objs:
            items = []
            for title, bsongs in objs:
                item = MusicListItem(title, list_type=MusicListItem.LOCAL_TYPE)
                songs = []
                for d in bsongs:
                    s = Song()
                    s.init_from_dict(d, cmp_key="sid")
                    songs.append(s)
                item.add_songs(songs)
                items.append(item)
            self.category_list.add_items(items, insert_pos=1)                    
            
    def new_listen_list(self):    
        
        def create_list(name):
            if name.strip():
                item = MusicListItem(name, list_type=MusicListItem.LOCAL_TYPE)
                self.category_list.add_items([item], insert_pos=1)
            
        input_dialog = InputDialog("新建试听列表", "", 300, 100,
                                   create_list)    
        input_dialog.show_all()
        
    def del_listen_list(self, item):        
        
        def del_list():
            if self.current_item == item:
                self.switch_view(self.default_list_item)                
            self.category_list.delete_items([item])
            self.save()
            
        ConfirmDialog("提示", "您确定要删除【%s】列表吗？" % item.title, 
                      confirm_callback=del_list).show_all()
    
    def on_viewbox_size_allocate(self, widget, rect):    
        ''' auto hide song_view's column when view_box's size changing '''
        
        if self.current_item:
            if rect.width > HIDE_PLAYLIST_WIDTH:
                self.current_item.song_view.set_hide_columns(None)
            else:    
                self.current_item.song_view.set_hide_columns([1])
                
    def on_event_login_success(self, obj, data):            
        ''' load online playlists when user login success '''
        
        self.load_online_lists()
        
    def on_event_collect_songs(self, obj, data):    
        self.collect_list_item.add_songs(data, pos=0)
        
    def on_event_add_songs(self, obj, data):    
        self.add_play_songs(data)
        
    def on_event_play_songs(self, obj, data):
        self.add_play_songs(data, play=True)
        
    def on_event_save_listen_lists(self, obj, data):    
        self.save()
        
    def add_play_songs(self, data, play=False):    
        if self.current_item.list_type not in (MusicListItem.DEFAULT_TYPE, MusicListItem.LOCAL_TYPE):
            self.switch_view(self.default_list_item)
            
        self.current_item.add_songs(data, play=play)
    
    def load_online_lists(self):
        if not bplayer.is_login:
            return 
            
        self.online_thread_id += 1
        thread_id = copy.deepcopy(self.online_thread_id)
        
        utils.ThreadFetch(
            fetch_funcs=(bplayer.get_playlists, ()),
            success_funcs=(self.render_online_lists, (thread_id,))
            ).start()
                                        
            
    @post_gui        
    def render_online_lists(self, playlists, thread_id):
        if self.online_thread_id != thread_id:
            return
                
        if len(playlists) > 0:
            items = [MusicListItem(data, list_type=MusicListItem.PLAYLIST_TYPE) 
                     for data in playlists]
            self.category_list.add_items(items)
            
    def del_online_list(self, item):        
        
        def bplayer_del_list():
            bplayer.del_list(item.list_id)
            if self.current_item == item:
                self.switch_view(self.default_list_item)                
            self.category_list.delete_items([item])
            
        ConfirmDialog("提示", "您确定要删除【%s】歌单吗？" % item.title, 
                      confirm_callback=bplayer_del_list).show_all()
        
    @login_required    
    def new_online_list(self):    
        
        def bplayer_new_list(name):
            self.new_list_thread_id += 1
            thread_id = copy.deepcopy(self.new_list_thread_id)
            utils.ThreadFetch(
                fetch_funcs=(bplayer.new_list, (name,)),
                success_funcs=(self.render_new_online_list, (thread_id,))
            ).start()
            
        input_dialog = InputDialog("新建歌单", "", 300, 100,
                                   bplayer_new_list)    
        input_dialog.show_all()
        
    @post_gui
    def render_new_online_list(self, data, thread_id):
        if self.new_list_thread_id != thread_id:
            return
        item = MusicListItem(data, list_type=MusicListItem.PLAYLIST_TYPE)
        self.category_list.add_items([item])
        
        
    def rename_online_list(self, item, is_online=True):    
        
        def bplayer_rename_list(name):
            if name.strip():
                item.set_title(name)
                if is_online:
                    bplayer.rename_list(item.list_id, name)
                else:    
                    self.save()
                
        input_dialog = InputDialog("重命名歌单", item.title, 300, 100,
                                   bplayer_rename_list)    
        input_dialog.show_all()
