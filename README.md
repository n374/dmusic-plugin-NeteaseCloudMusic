百度音乐插件(深度音乐播放器)
========================

特性
--------
* 支持百度账号登录 
* 可以管理本地试听列表
* 可以管理在线歌单
* 支持收藏歌曲并同步
* 高质量音频(320kbps)

LinuxDeepin系统安装方法
----------------------
1. 安装依赖
```
sudo apt-get install python-javascriptcore git
```

2. 安装百度音乐插件
```
git clone https://github.com/sumary/dmusic-plugin-baidumusic.git
cd dmusic-plugin-baidumusic
cp -r baidumusic ~/.local/share/deepin-music-player/plugins/
```

其它Linux发行版
------------------

1. 安装 cython libwebkitgtk-dev python-dev git, 例如:
```
sudo apt-get install cython libwebkitgtk-dev python-dev git
```

2. 安装pyjavascriptcore
```
git clone https://github.com/sumary/pyjavascriptcore.git
cd pyjavascriptcore
sudo python setup.py install
```

3. 安装百度音乐插件
```
git clone https://github.com/sumary/dmusic-plugin-baidumusic.git
cd dmusic-plugin-baidumusic
cp -r baidumusic ~/.local/share/deepin-music-player/plugins/
```

使用
----

运行深度音乐， 选项设置->附加组件 中启用百度音乐即可


贡献者
-------

* [@lovesnow](https://github.com/lovesnow)
* [@binyuj](https://github.com/binyuj)

