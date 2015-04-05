#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os
import shutil

def copytree(src, dst):
    """Recursively copy a directory tree using copy2().

    Modified from shutil.copytree

    """
    base = os.path.basename(src)
    dst = os.path.join(dst, base)
    names = os.listdir(src)
    if not os.path.exists(dst):
        os.makedirs(dst)
    for name in names:
        srcname = os.path.join(src, name)
        try:
            if os.path.isdir(srcname):
                copytree(srcname, dst)
            else:
                shutil.copy2(srcname, dst)
        except Exception ,e:
            print e
            raise

def softlink(src, dst):
    link_dst = os.path.join(dst, src.rsplit('/', 1)[-1])
    if os.path.exists(link_dst):
        os.system("rm -rf %s" % link_dst)

    if not os.path.exists(dst):
        os.makedirs(dst)
    os.system("ln -s %s %s" % (src, dst))

if __name__ == "__main__":
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
            'neteasecloudmusic')
    dst = os.path.join(os.path.expanduser("~"), ".local", "share", "deepin-music-player", "plugins")
    softlink(src, dst)
