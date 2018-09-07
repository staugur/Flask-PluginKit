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


### 资源(Resources)

* `GitHub` <https://github.com/staugur/Flask-PluginKit>
* `Author` <https://www.saintic.com>
* `Docs` <http://docs.saintic.com/754273>
* `Issues` <https://github.com/staugur/Flask-PluginKit/issues>


### 文档(Documentation)

[点击这(Click here)](http://docs.saintic.com/754273)


### LICENSE

[MIT LICENSE](http://flask.pocoo.org/docs/license/#flask-license)
