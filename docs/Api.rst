Restful api returns the json format
-----------------------------------

    * Return json data, public return: {"msg": null, "code": int}
    * When code is 0, the request is successful; non-zero is the request failure, at this time, msg has a failure message.

flask_pluginkit
---------------

.. automodule:: flask_pluginkit.flask_pluginkit
    :members: PluginManager, push_dcp
    :undoc-members:
    :show-inheritance:
    :noindex:

installer
----------

.. automodule:: flask_pluginkit.installer
    :members: PluginInstaller
    :undoc-members:
    :show-inheritance:
    :noindex:

web
---

.. automodule:: flask_pluginkit.web
    :members: blueprint
    :undoc-members:
    :show-inheritance:
    :noindex:

fixflask
--------

.. automodule:: flask_pluginkit.fixflask
    :members: Flask
    :undoc-members:
    :show-inheritance:
    :noindex:

utils
-----

.. automodule:: flask_pluginkit.utils
    :members: BaseStorage, LocalStorage, RedisStorage, PY2, string_types
    :undoc-members:
    :show-inheritance:
    :noindex:

exceptions
----------

.. autoexception:: flask_pluginkit.PluginError
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:

.. autoexception:: flask_pluginkit.TarError
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:

.. autoexception:: flask_pluginkit.ZipError
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:

.. autoexception:: flask_pluginkit.InstallError
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:

.. autoexception:: flask_pluginkit.CSSLoadError
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:

.. autoexception:: flask_pluginkit.DCPError
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:
