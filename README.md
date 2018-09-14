# Flask-PluginKit

基于Flask的插件式开发工具(Web program plugin development kit based on flask).


### 使用概述(Overview)

安装(Installation)

```
$ pip install flask-pluginkit
```

普通模式(Usage)

```
from flask_pluginkit import PluginManager
plugin = PluginManager(app)
```

工厂模式(The factory pattern)

```
from flask_pluginkit import PluginManager
plugin = PluginManager()
plugin.init_app(app)
```


### TODO

- ~~before_request_return扩展点~~
- 注册上下文扩展点
- 注册静态css(register_css)
- 模板扩展点include改造
- 信号扩展点sep
- 插件Web管理页面


### 资源(Resources)

* GitHub [https://github.com/staugur/Flask-PluginKit](https://github.com/staugur/Flask-PluginKit "https://github.com/staugur/Flask-PluginKit")
* Author [https://www.saintic.com](https://www.saintic.com "https://www.saintic.com")
* Docs [http://docs.saintic.com/754273](http://docs.saintic.com/754273 "http://docs.saintic.com/754273")
* Issues [https://github.com/staugur/Flask-PluginKit/issues](https://github.com/staugur/Flask-PluginKit/issues "https://github.com/staugur/Flask-PluginKit/issues")


### 文档(Documentation)

[点击这(Click here)](http://docs.saintic.com/754273)


### LICENSE

[MIT LICENSE](http://flask.pocoo.org/docs/license/#flask-license)
