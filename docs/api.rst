.. _api:

API
===

.. module:: flask_pluginkit

This part of the documentation covers all the interfaces of Flask-PluginKit.


PluginManager Object
--------------------

.. autoclass:: PluginManager
    :members:

    .. automethod:: __init__
    .. automethod:: init_app
    .. automethod:: _tep_handler
    .. automethod:: _hep_handler
    .. automethod:: _bep_handler
    .. automethod:: _vep_handler

Inherited Application Objects
-----------------------------

.. autoclass:: Flask
    :members:


Storage Objects
----------------

.. autoclass:: LocalStorage
    :members:

    .. attribute:: index

        The default index, as the only key, you can override it.

.. autoclass:: RedisStorage
    :members:

    .. attribute:: index

        The default index, as the only key, you can override it.


Useful Functions and Classes
----------------------------

.. currentmodule:: flask_pluginkit.utils

.. autofunction:: isValidSemver

.. autofunction:: sortedSemver

.. autoclass:: BaseStorage
    :members:

.. currentmodule:: flask_pluginkit

.. autoclass:: PluginInstaller
    :members:

Custom Exceptions
-----------------

.. automodule:: flask_pluginkit.exceptions
    :members:
    :show-inheritance:
