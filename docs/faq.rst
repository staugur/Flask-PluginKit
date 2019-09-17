FAQ
===

.. _faq-cov:

Compatible with older versions
------------------------------

When the original v3.x was refactored, it was not compatible with the old
version, namely v2.x, so the old plugins need to be updated one by one.

The old version requires the plugin to return a class through the
``getPluginClass`` function, and write the method to register tep, bep, hep,
etc in the class, so you only need to return the above method through the
``register`` function when updating the plugin, for example:

Legacy plugin code:

.. code-block:: python

    def getPluginClass():
        return MyPluginClass

    class MyPluginClass(object):

        def _after_func(self, response):
            pass

        def run(self):
            pass

        def register_tep(self):
            return {
                "after_request_hook": self._after_func,
                "before_request_hook": xx
            }

        def register_bep(self):
            return {}

        def register_hep(self):
            return {}

        def register_yep(self):
            return {}

        def register_dfp(self):
            return {}

Compatibility modification (add the following code):

.. code-block:: python

    def register():
        mpc = MyPluginClass()
        return dict(
            tep=mpc.register_tep(),
            bep=mpc.register_bep(),
            hep={"after_request": mpc._after_func, "before_request": xx, ...},
        )

.. note::
    - The new version does not support yep, dfp, but instead of other methods.

    - hep removed the suffix ``_hook`` in the new version.

    - The after_request and teardown_request in hep, pay attention to the
      parameter changes of the function.

However, in v3.3.1, the auto-compatible code has been added.
Flask-PluginKit tries to load and convert the old version of tep, bep, and hep
according to the parameters during loading, so the plugin can be modified
without compatibility.
