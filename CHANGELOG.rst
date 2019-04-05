
V2.3.0
------

Released in 2019-04-05

- 支持推送扩展函数
- 更新文档
- 更新dcp回调函数检测

V2.2.0
------

Released in 2019-04-03

-  支持本地插件和第三方插件


V2.1.1
------

Released in 2018-12-06

-  修复插件版本号的问题

V2.1.0
------

Released in 2018-11-02

-  修复bug，并将移除旧版本
-  添加动态连接点(dcp)，可以为某个标识点添加、删除函数并在模板种获取标识点函数执行的结果(HTML代码)
-  更改 ``register_cep`` 为 ``register_hep``, 请确保更改，谨慎升级
-  更新文档

V2.0.0
------

Released in 2018-10-27

-  支持Python3
-  尽可能完整的文档
-  存储索引由 ``flask_pluginkit.db`` 改为 ``flask_pluginkit_dat``
-  插件元数据中插件名称由 ``__name__`` 改为 ``__plugin_name__``, 以避免与python冲突, 请谨慎升级到此版本

V1.3.0
------

Released in 2018-10-15

-  简单存储服务，用来给插件提供数据存储和读取
-  本地存储和redis存储
-  自定义存储

V1.2.0
------

Released in 2018-10-11

-  模板排序
-  支持HTTP Basic Auth认证方式

V1.0.2
------

Released in 2018-10-09

-  重载uwsgi

V1.0.1
------

Released in 2018-10-08

-  修复插件依赖于before_request的问题
-  集成支持多静态文件夹

V1.0.0
------

Released in 2018-09-27

-  使用sphinx制作接口文档

V0.1.10
-------

Released in 2018-09-25

-  调整register_yep，改为更灵活的方式分类载入css文件
-  支持emit_tep渲染模板时传递额外数据
-  优化部分代码

V0.1.9
------

Released in 2018-09-24

-  修复bug
-  插件Web管理页面：支持认证

V0.1.8
------

Released in 2018-09-22

-  层叠样式表扩展点，可在模板中引用
-  模板扩展点使用更改，去除get_tep、get_tep_string，使用emit_tep代替，支持包含模板和HTML代码

V0.1.7
------

Released in 2018-09-20

-  修复bug
-  不支持python2.6

V0.1.6
------

Released in 2018-09-19

-  插件Web管理页面：启用、禁用插件，重启应用

V0.1.4
------

Released in 2018-09-09

-  Add ``before_request_return`` CEP

V0.1.3
------

-  Flask扩展，以支持应用插件式开发
-  支持上下文扩展点、模板扩展点、蓝图扩展点
-  模板扩展点支持HTML代码和文件
-  插件支持添加静态文件(需要安装\ ``flask-multistatic``\ 扩展)
-  插件安装管理(从url或local安装插件zip、gz包)
