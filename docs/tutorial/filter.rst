.. _filter:

Template Filter Extension Point
===============================

Description
-----------

The extension point abbreviation is filter.

The concept of template filters comes from jinja2, which is essentially a
regular python function. The filter and variables are separated by a
pipe symbol ( | ), and optional parameters can also be passed in parentheses.
The left side of the filter is used as the first parameter,
and the remaining parameters are passed to the filter as
additional parameters or keyword parameters.

The plugin needs to return the filter field via register. The data type of
this field can be dict or list.
If it is a dict, the format is {filter_name: func}.
If it is a list, the format is [func1, func2], and the function name is
used as the filter name, but if an anonymous function is used,
the filter name is <lambda>, which is unfriendly!

So, if the format is list, the element type is allowed to be tuple, ie:
[func1, (name, func2)], thus setting the name of the filter.

The Flask-PluginKit loads filter via
:meth:`~flask_pluginkit.PluginManager._filter_handler`, this method will
detect filter rules and specific content.

Once the registration is complete, you can use the filter in the template
like Jinja2's built-in filter. For this section, you can refer to the
Jinja2 documentation `filters`_.

.. _filters: http://jinja.pocoo.org/docs/templates/#filters

Example
-------

- Plugin registration for filter

.. code-block:: python

    def reverse_filter(s):
        return s[::-1]

    def register():
        return dict(
            filter=dict(reverse=reverse_filter)
        )

- Call in template

.. code-block:: html

    <div>
        {% for x in ['m','y', 'l', 'i', 's', 't'] | reverse %}
            {{ x }}
        {% endfor %}
    </div>

