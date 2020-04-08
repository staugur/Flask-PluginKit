.. _cvep:

Class-based View Extension Point
================================

Description
-----------

The extension point abbreviation is cvep.

Flask-Classful is an extension that adds class-based views to Flask.

This extension point is flask-classful based to extend routing, so your
application needs to install it (document url is: `flask_classful_docs`_):

.. code-block:: bash

    $ pip install -U Flask-Classful

The plugin needs to return the cvep field via register. The returned cvep data
type can be dict, list or tuple, em, the format is similar to vep.

The dict format is {view_class:, other register options}, see the
`flask_classful_register`_ for more options, a common example is:

.. code-block:: python

    from flask_classful import FlaskView

    class TestView(FlaskView):

        def index(self):
            return "test"

    dict(view_class=TestView, route_base="/classful")

Other types are represented as multiple routes,
and multiple dict data of the above type can be nested.

The Flask-PluginKit loads cvep via
:meth:`~flask_pluginkit.PluginManager._cvep_handler`, this method will
detect cvep rules and specific content.

.. _flask_classful_docs: http://flask-classful.teracy.org/
.. _flask_classful_register: http://flask-classful.teracy.org/#flask_classful.FlaskView.register
.. _add_url_rule: http://flask.palletsprojects.com/api/#flask.Flask.add_url_rule

Example
-------

- Plugin registration for cvep

.. code-block:: python

    from flask_classful import FlaskView

    quotes = [
        "A noble spirit embiggens the smallest man! ~ Jebediah Springfield",
        "If there is a way to do it better... find it. ~ Thomas Edison",
        "No one knows what he can do till he tries. ~ Publilius Syrus"
    ]

    class QuotesView(FlaskView):

        def index(self):
            """Visit: http://localhost:5000/quotes/"""
            return "<br>".join(quotes)

        def get(self, id):
            """Visit: http://localhost:5000/quotes/1/"""
            id = int(id)
            if id < len(quotes) - 1:
                return quotes[id]
            else:
                return "Not Found", 404

    def register():
        return dict(
            cvep = [
                dict(view_class=QuotesView)
            ]
        )
