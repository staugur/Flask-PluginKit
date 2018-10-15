# Flask-PluginKit

基于Flask的插件式开发工具(Web program plugin development kit based on flask).

[![Build Status](https://travis-ci.com/staugur/Flask-PluginKit.svg?branch=master)](https://travis-ci.com/staugur/Flask-PluginKit) [![Join the chat at https://gitter.im/staugur/Lobby](https://badges.gitter.im/staugur/Lobby.svg)](https://gitter.im/staugur/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![GitHub](https://img.shields.io/github/license/mashape/apistatus.svg?style=popout)](https://pypi.org/project/Flask-PluginKit/) [![PyPI](https://img.shields.io/pypi/v/Flask-PluginKit.svg?style=popout)](https://pypi.org/project/Flask-PluginKit/) [![Documentation Status](https://readthedocs.org/projects/flask-pluginkit/badge/?version=latest)](https://flask-pluginkit.readthedocs.io/en/latest/?badge=latest)


### 使用概述(Overview)

安装(Installation)

```bash
# 正式版(Release)
$ pip install -U Flask-PluginKit
# 开发版(Dev)
$ pip install -U https://github.com/staugur/Flask-PluginKit/archive/master.tar.gz
```

测试用例(TestCase)

```bash
$ make test
```

普通模式(Usage)

```python
from flask_pluginkit import PluginManager
plugin = PluginManager(app)
```

工厂模式(The factory pattern)

```python
from flask_pluginkit import PluginManager
plugin = PluginManager()
plugin.init_app(app)
```


### TODO

- ~~before_request_return扩展点~~
- ~~注册静态css(register_css)~~
- ~~注册静态css时分类~~
- ~~模板扩展点include改造~~
- ~~插件Web管理页面~~
- ~~web blueprint auth(only BOOL, after extension)~~
- ~~sphix rst docs~~
- ~~允许重载uwsgi~~
- ~~添加http basic auth等其他认证~~
- ~~模板上下文排序~~
- 插件配置和插件信息存储
- 注册上下文扩展点
- 注册程序任意位置扩展点
- 信号扩展点sep
- Web管理页面插件安装和删除
- 允许使用requirements.txt安装额外的包
- 自定义web认证


### 资源(Resources)

* GitHub [https://github.com/staugur/Flask-PluginKit](https://github.com/staugur/Flask-PluginKit "https://github.com/staugur/Flask-PluginKit")
* Author [https://www.saintic.com](https://www.saintic.com "https://www.saintic.com")
* Issues [https://github.com/staugur/Flask-PluginKit/issues](https://github.com/staugur/Flask-PluginKit/issues "https://github.com/staugur/Flask-PluginKit/issues")


### 文档(Documentation)

[使用教程(Click here)](http://docs.saintic.com/754273)

[Api文档(Click here)](https://flask-pluginkit.readthedocs.io)


### LICENSE

[MIT LICENSE](http://flask.pocoo.org/docs/license/#flask-license)
