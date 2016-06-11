#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Song(object):

    def __init__(self, data):
        self.song_id = data["id"]
        self.song_name = data["name"]

        self.artist_names = ','.join([ar["name"] for ar in data["ar"]])
        self.artist_ids = [ar["id"] for ar in data["ar"]]

        self.album_name = data["al"]["name"]
        self.album_pic = data["al"]["picUrl"]

        self.length = str(data["dt"]/60000) + "分" \
                + str((data["dt"]%60000)/1000) + "秒"

        if data["h"]:
            self.fid = data["h"]["fid"]
        elif data["m"]:
            self.fid = data["m"]["fid"]
        else:
            self.fid = data["l"]["fid"]
