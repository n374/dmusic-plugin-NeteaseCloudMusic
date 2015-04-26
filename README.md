网易云音乐插件(深度音乐播放器)
========================

基于sumary的[dmusic-plugin-baidumusic](https://github.com/sumary/dmusic-plugin-baidumusic)修改而成

使用了[NetEaseMusicBox](https://github.com/bluetomlee/NetEase-MusicBox)中的网易云音乐[API](https://github.com/bluetomlee/NetEase-MusicBox/blob/master/src/api.py)


特性
--------


支持网易账号及手机号登录，支持新浪微博账号及二维码登录

播放创建的歌单、收藏的歌单

播放私人FM

支持从网易获取歌词及封面

![](https://raw.githubusercontent.com/wu-nerd/dmusic-plugin-NeteaseCloudMusic/master/neteasecloudmusic/images/screenshot003.png)
![](https://raw.githubusercontent.com/wu-nerd/dmusic-plugin-NeteaseCloudMusic/master/neteasecloudmusic/images/screenshot004.png)

安装方法
----------------------
- **安装深度音乐播放器**
```
sudo apt-add-repository ppa:noobslab/deepin-sc
sudo apt-get update
sudo apt-get install deepin-music-player
```
- **安装Requests库**

部分发行版的Python没有自带Requests库，如[openSUSE 13.2](https://github.com/wu-nerd/dmusic-plugin-NeteaseCloudMusic/issues/3)，请手动安装
```
sudo pip install requests
```
或者参照[官方文档](http://docs.python-requests.org/en/latest/user/install/#install)


- **安装网易云音乐插件**
```
git clone https://github.com/wu-nerd/dmusic-plugin-NeteaseCloudMusic.git
cd dmusic-plugin-NeteaseCloudMusic
python install.py
```

使用
----

运行深度音乐， 选项设置->附加组件 中启用网易云音乐即可
