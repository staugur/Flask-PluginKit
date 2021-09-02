Foreword
========

What?
-----

Flask-PluginKit is a Flask extension for extending web application
functionality. It provides an easy way to create plugins for your application.
It is possible to create extension points which can then be used to
extend your application without the need to modify your core code.

Flask-PluginKit can also be said to be a glue, or a bridge, for
connecting web and web plugins. It supports native plugins and
third-party plugins from pypi, git, svn, and so on. In addition, the plugin
is also very simple to write.

Glossary
--------

The following is a Chinese-English comparison:

Extension Point
    扩展点

TEP / tep / Template Extension Point
    模板扩展点

HEP / hep / Hook Extension Point
    钩子扩展点

BEP / bep / Blueprint Extension Point
    蓝图扩展点

VEP / vep / View function Extension Point
    视图扩展点

DCP / dcp / Dynamic Connection Point
    动态连接点

TCP / tcp / Template Context Processor / Context Processor
    模板上下文处理器扩展点

filter
    模板过滤器扩展点

errhandler
    错误处理器扩展点

p3
    插件预处理器

Developer / developer
    插件开发者

Local Plugin
------------

It is a local directory, it should be located in the plugins directory of
the web application (of course, can also be defined as other directories),
and is a legal python package, that is: plugins contain ``__init__.py`` files,
plugiin directories also Contains ``__init__.py``, this file identifies
the directory as a package, and also identifies the plugin,
which is the core code, plugin entry.

Third-party Plugin
------------------

Third-party plugins are non-web application subdirectories, but
local modules from installations such as pip or easy_install.

The third-party plugins are free to use. The web application does not need
to put the plugin code into a subdirectory. It only needs to be installed
to the local machine using `pip install` or `easy_install`, and then pass
the :attr:`~flask_pluginkit.PluginManager.plugin_packages` parameter when
the :class:`~flask_pluginkit.PluginManager` is initialized.

This means that anyone can write a package and publish it to pypi;
the user writes `requirements.txt` and installs the dependencies,
which are called in the initialization, in one go, and almost no need
to worry about subsequent third-party plugin upgrades.

For instructions on how to write third-party plugins,
see :doc:`/tutorial/third-party-plugin`

For official plugin's github group: https://github.com/saintic

Loading logic
-------------

Developers who are not Flask-PluginKit or its plugins can ignore this part.

The plugin load starts when the program starts.
The load class is :class:`~flask_pluginkit.PluginManager`,
its destructor allows you to pass
:attr:`~flask_pluginkit.PluginManager.plugins_base`
(the default program directory),
:attr:`~flask_pluginkit.PluginManager.plugins_folder`
(the directory where the plugin is located),
set the plugin absolute path directory, and also support factory mode,
see the API documentation for more parameters.

The loading process is as follows:

1. Call :class:`~flask_pluginkit.PluginManager` normal mode or factory mode
   to initialize the extension.

2. Scan the `plugins_folder` plugin directory and the packages that
   match the plugin rules will be dynamically loaded.

3. Load third-party plugins in
   :attr:`~flask_pluginkit.PluginManager.plugin_packages`.

4. Add template global variable.

5. Support for multiple template directories.

6. Add a view function that supports access to
   plugin directory static resources.

7. Register hep, bep.

8. Append the instance to **app.extensions**.
