网易云音乐插件(深度音乐播放器)
========================

基于sumary的[dmusic-plugin-baidumusic](https://github.com/sumary/dmusic-plugin-baidumusic)修改而成

使用了[NetEaseMusicBox](https://github.com/bluetomlee/NetEase-MusicBox)中的网易云音乐[API](https://github.com/bluetomlee/NetEase-MusicBox/blob/master/src/api.py)


特性
--------

~~目前仅支持通过用户id播放用户的歌单~~

支持网易账号登录

安装方法
----------------------
- **安装深度音乐播放器**
```
sudo apt-add-repository ppa:noobslab/deepin-sc
sudo apt-get update
sudo apt-get install deepin-music-player
```

- **安装网易云音乐插件**
```
git clone https://github.com/wu-nerd/dmusic-plugin-NeteaseCloudMusic.git
cd dmusic-plugin-NeteaseCloudMusic
python install.py
```

使用
----

运行深度音乐， 选项设置->附加组件 中启用网易云音乐即可
