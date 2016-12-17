网易云音乐插件(深度音乐播放器)
========================

基于sumary的[dmusic-plugin-baidumusic](https://github.com/sumary/dmusic-plugin-baidumusic)修改而成

使用了[NetEaseMusicBox](https://github.com/bluetomlee/NetEase-MusicBox)中的网易云音乐[API](https://github.com/bluetomlee/NetEase-MusicBox/blob/master/src/api.py)

非大陆用户可能无法播放音乐，请使用proxychains设置播放器代理或使用VPN


特性
--------


- 支持网易账号及手机号登录，支持新浪微博账号及二维码登录

- 播放创建的歌单、收藏的歌单

- 支持搜索、添加、删除歌曲

- 支持搜索、添加、删除歌单

- 播放私人FM，支持红心、取消红心、删除歌曲

- 支持每日歌曲推荐

- 支持从网易获取歌词及封面

- ~~在自行添加歌曲id加密代码的情况下可以实现320K，[详见](https://github.com/wu-nerd/dmusic-plugin-NeteaseCloudMusic/issues/5#issuecomment-99753615)~~ 已失效

![](https://raw.githubusercontent.com/wu-nerd/dmusic-plugin-NeteaseCloudMusic/master/neteasecloudmusic/images/screenshot006.png)
![](https://raw.githubusercontent.com/wu-nerd/dmusic-plugin-NeteaseCloudMusic/master/neteasecloudmusic/images/screenshot007.png)

安装方法
----------------------
- **安装深度音乐播放器**
```
sudo apt-add-repository ppa:noobslab/deepin-sc
sudo apt-get update
sudo apt-get install deepin-music-player
```
这个源有段时间没有更新，因此Ubuntu 15.04可能无法安装。需要修改`/etc/apt/sources.list.d`文件夹下`noobslab-ubuntu-deepin-sc-vivid.list`文件，将其中的的`vivid`修改成`utopic`，然后
```
sudo apt-get update
sudo apt-get install deepin-music-player
```

安装完成后恢复原样

- **安装Requests库及pycrypto库**
```
sudo apt-get install python-pip
sudo pip install requests
sudo pip install pycrypto
```

对于默认使用Python 3的发行版比如Arch，请安装python2版本的库：
```
sudo pacman -Ss python2-pip
sudo pip2 install requests
sudo pip2 install pycrypto
```

- **安装网易云音乐插件**
```
git clone https://github.com/wu-nerd/dmusic-plugin-NeteaseCloudMusic.git
cd dmusic-plugin-NeteaseCloudMusic
python2 install.py
```

使用
----

运行深度音乐， 选项设置->附加组件 中启用网易云音乐即可
