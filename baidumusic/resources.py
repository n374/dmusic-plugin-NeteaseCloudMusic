#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
from netlib import Curl
from utils import parser_json, threaded
from song import Song
import base64
import json

TAGS_MUSIC_KEYS = {
    "song_id" : "sid",
    "song_title" : "title",
    "song_artist" : "artist",
    "album_title" : "album",
    "album_pic_small" : "album_url",
    "lyric_url" : "lyric_url",
    "url" : "uri",
    "kbps" : "#rate",
    "duration" : "#duration",
    "url_expire_time" : "uri_expire_time",
    "append" : "is_append",
    "version" : "version",
    "resource_source" : "resource_source",
    "copy_type" : "copy_type",
    
    # collect songs
    "title" : "title",
    "artist" : "artist",
    "album" : "album",
    "album_id" : "album_id",
    
    # list songs
    "file_duration" : "#duration",
    "author" : "artist",
    "lrclink" : "lyric_url",
}

public_curl = Curl()

    
def parse_to_dsong(ret, song=None):
    is_dummy = False
    
    if song is None:
        song = dict()
        is_dummy = True
        
    try:
        bsong = ret
        file_list = bsong.pop("file_list", [])
        if len(file_list) > 0:
            bfile = file_list[0]
            bsong.update(bfile)
        
        for btag, tag in TAGS_MUSIC_KEYS.iteritems():
            if bsong.has_key(btag):
                if btag in ("duration", "file_duration"):
                    try:
                        song[tag] = int(bsong[btag])  * 1000
                    except:    
                        song[tag] = 0
                else:    
                    song[tag] = bsong[btag]
                    
    except Exception, e:            
        import sys
        import traceback
        traceback.print_exc(file=sys.stdout)
        return None
    else:
        song["fetch_time"] = time.time()
        
        if is_dummy:
            new_song = Song()
            new_song.init_from_dict(song, cmp_key="sid")
            new_song.set_type('baidumusic')
            return new_song
        return song
    
class BaseInterface(object):
    
    @property
    def common_kwargs(self):
        return {"format" : "json", "from" : "bmpc",
                "clientVer" : "8.3.4.5",
                "bduss" : self.bduss}

    def request_songinfo(self, song):
        url = "http://musicmini.baidu.com/app/link/getLinks.php"
        data = dict(songId=song['sid'],
                    songArtist=song['artist'],
                    songTitle=song['title'],
                    linkType=self.link_type,
                    isLogin=self.is_login,
                    clientVer=self.client_version,
                    isCloud=self.is_cloud,
                    isHq=self.is_hq_enabled
                    )
        params = {'param' : base64.b64encode(json.dumps(data))}
        ret = public_curl.request(url, params, method="POST")
        pret = parser_json(ret)
        if len(pret) > 0:
            return parse_to_dsong(pret[0], song)
        return None
    
    def request_userinfo(self):
        url = "http://musicmini.baidu.com/api/index.php"
        data = {"ver" : 1, "type" : 2, "format" : "json",
                "clientver" : self.client_version,
                "from" : "baidumusic",
                "bduss" : self.bduss}
        ret = public_curl.request(url, data)
        return parser_json(ret)

    def restserver_request(self, method, **kwargs):
        data = {}
        data.update(self.common_kwargs)
        data.update(kwargs)
        data["method"] = method
        
        url = "http://tingapi.ting.baidu.com/v1/restserver/ting"
        ret = public_curl.request(url, data)
        return parser_json(ret)
        
    def get_playlists(self):
        ret = self.restserver_request("ting.baidu.diy.getPlaylists")
        return ret.get("play_list", [])

    def get_playlist_songs(self, pid, pn=0, rn=100):
        data = self.restserver_request("ting.baidu.diy.getPlaylist", 
                                       id=pid, with_song=1, pn=pn, rn=rn)
        bsongs = data.get("songlist", [])
        return self.parse_dummy_songs(bsongs, False)
    
    def get_collect_songs(self, pn=0, rn=100):
        data = self.restserver_request("baidu.ting.favorite.getCollectSong", pn=pn, rn=rn)
        have_more = data.get("havemore", 0)
        bsongs = data.get("result", [])
        return (self.parse_dummy_songs(bsongs, False), have_more)
    
    @threaded
    def add_collect_song(self, song_id):
        return self.restserver_request("baidu.ting.favorite.addSongFavorites",
                                       songId=song_id)
    @threaded        
    def del_collect_song(self, song_id):
        
        ret= self.restserver_request("baidu.ting.favorite.delCollectSong", 
                                       songId=song_id)
        return ret
    
    @threaded
    def add_list_song(self, list_id, song_id):
        ret =  self.restserver_request("baidu.ting.diy.addListSong", 
                                       listId=list_id, songId=song_id)
        return ret
    
    @threaded
    def del_list_song(self, list_id, song_id):
        ret = self.restserver_request("baidu.ting.diy.delListSong", 
                                       listId=list_id, songId=song_id)
        return ret
    

    @threaded
    def rename_list(self, list_id, title):
        return self.restserver_request("baidu.ting.diy.upList",
                                       listId=list_id, title=title)
    
    def new_list(self, title):
        data = self.restserver_request("baidu.ting.diy.addList",
                                       title=title)
        
        lid = data.get("result", {}).get("listId", None)
        if lid:
            return {"id" : lid, "title" : title}
        
    @threaded    
    def del_list(self, list_id):
        return self.restserver_request("baidu.ting.diy.delList",
                                       listId=list_id)
    
    def get_mv(self, song_id):
        url = "http://musicmini.baidu.com/app/mv/getMV.php"
        data = dict(songid=song_id)
        ret = public_curl.request(url, data)
        return parser_json(ret)
    
    
    def get_bduss(self):
        url = "http://musicmini.baidu.com/app/passport/getBDUSS.php"
        return public_curl.request(url)
        
