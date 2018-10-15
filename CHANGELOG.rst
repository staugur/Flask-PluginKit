CHANGELOG
=========

V1.3.0
------

Released in 2018-10-15

-  Simple Storage Service(s3) for local and redis
-  The custom storage for s3

V1.2.0
------

Released in 2018-10-11

-  The template sequence
-  Support HTTP Basic Auth

V1.0.2
------

Released in 2018-10-09

-  reload uwsgi

V1.0.1
------

Released in 2018-10-08

-  Fix the problem that the plug-in relies on before_request
-  Integration supports static multiple folders

V1.0.0
------

Released in 2018-09-27

-  make docs with sphinx

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
-  模板扩展点使用更改，去除get_tep、get_tep_strin，使用emit_tep代替，支持包含模板和HTML代码

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