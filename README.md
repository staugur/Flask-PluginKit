# Flask-PluginKit

基于Flask的插件式开发工具(Web program plugin development kit based on flask).

[![Build Status](https://travis-ci.com/staugur/Flask-PluginKit.svg?branch=master)](https://travis-ci.com/staugur/Flask-PluginKit) [![Documentation Status](https://readthedocs.org/projects/flask-pluginkit/badge/?version=latest)](https://flask-pluginkit.readthedocs.io/) [![codecov](https://codecov.io/gh/staugur/Flask-PluginKit/branch/master/graph/badge.svg)](https://codecov.io/gh/staugur/Flask-PluginKit) [![GitHub](https://img.shields.io/github/license/mashape/apistatus.svg?style=popout)](https://pypi.org/project/Flask-PluginKit/) [![PyPI](https://img.shields.io/pypi/v/Flask-PluginKit.svg?style=popout)](https://pypi.org/project/Flask-PluginKit/) [![Pyversions](https://img.shields.io/pypi/pyversions/flask-pluginkit.svg
)](https://pypi.org/project/Flask-PluginKit)

### 使用概述(Overview)

安装(Installation)

```bash
# 正式版(Release)
$ pip install -U Flask-PluginKit
# 开发版(Dev)
$ pip install -U git+https://github.com/staugur/Flask-PluginKit.git
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
- ~~插件配置和插件信息存储~~
- ~~动态连接点，动态注册并执行函数将结果返回给模板使用~~
- ~~插件版本号检测是否符合语义化版本2.0标准~~
- 请求扩展点，请求上下文环境中执行一个函数
- Web管理页面插件安装和删除
- 允许使用requirements.txt安装额外的包
- 自定义web认证
- web认证黑白名单
- 模板代码、文件优先级


### 资源(Resources)

* GitHub [https://github.com/staugur/Flask-PluginKit](https://github.com/staugur/Flask-PluginKit "https://github.com/staugur/Flask-PluginKit")
* 码云 [https://gitee.com/staugur/Flask-PluginKit](https://gitee.com/staugur/Flask-PluginKit "https://gitee.com/staugur/Flask-PluginKit")
* Author [https://www.saintic.com](https://www.saintic.com "https://www.saintic.com")
* Issues [https://github.com/staugur/Flask-PluginKit/issues](https://github.com/staugur/Flask-PluginKit/issues "https://github.com/staugur/Flask-PluginKit/issues")
* 使用 *Flask-PluginKit* 的项目 [https://github.com/topics/flask-pluginkit](https://github.com/topics/flask-pluginkit "https://github.com/topics/flask-pluginkit")


### 文档(Documentation)

* [中文](https://flask-pluginkit.readthedocs.io/zh_CN/latest/)

* [English](https://flask-pluginkit.readthedocs.io/en/latest/)


### 许可证(LICENSE)

[MIT LICENSE](http://flask.pocoo.org/docs/license/#flask-license)


### 说在后面(END)

欢迎提交PR、共同开发！


