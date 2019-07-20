.. _tep:

Template Extension Point
========================

Description
-----------

The extension point abbreviation is tep.

As the name implies, tep only works in the template environment.
It is used to enhance or extend existing templates.
It can be simple html code or complex html files.
It needs to be manually called by the user in the existing template.

The plugin needs to return the tep field via register. The tep data type
returned is a dictionary with the format {tep_name: html_code_or_file},
which can have multiple tep_names.

The Flask-PluginKit loads tep via
:meth:`~flask_pluginkit.PluginManager._tep_handler`, this method will
detect tep rules and specific content. The value corresponding to tep_name is
recognized as a template file if it ends with **.html**, **.htm**, **.xhtml**,
otherwise it is a simple html code.

Although the tep_name in the tep returned by each plugin is unique, since a
web application can have multiple plugins, the tep_name can contain not only
the html code but also the template file for the entire web application.

In use, in the existing template, all contents corresponding to tep_name are
called by :meth:`~flask_pluginkit.PluginManager.emit_tep`, the template file
is rendered by :func:`flask.render_template`, and the html code is rendered by
:func:`flask.render_template_string`, which means that the html code can also
be supported by jinja2 like a template file, jinja2 syntax, functions, macros,
etc. In addition, use emit_tep to pass in the typ parameter settings to
render only html code or files, and also pass in other keyword parameters
as context data for rendering.

.. tip::

    The template file supports sorting. You need to pass
    :attr:`~flask_pluginkit.PluginManager.stpl` is True when
    initializing the :class:`~flask_pluginkit.PluginManager`.
    The usage is "sort-field\@template-file".

.. note::

    It is recommended that you create a new directory to store html files
    under the plugin templates. Because the Flask-PluginKit only loads the
    templates directory under the plugin, and does not guarantee template
    conflicts, the new directory can avoid conflicts with other plugin
    template files, which can not be referenced properly.

Example
-------

- Plugin registration for tep

.. code-block:: python

    def register():
        return dict(
            tep=dict(
                base_header="example/header.html",
                base_footer="Copyright 2019."
            )
        )

As above, you need to create a new "templates/example" directory in the plugin
directory, and put header.html into the directory. If it does not exist, the
exception :class:`~flask_pluginkit.exceptions.TemplateNotFound`
will be thrown.

- User call

In the existing template, assume that the following file named base.html is
the base template, user need to manually call
:meth:`~flask_pluginkit.PluginManager.emit_tep`, can pass additional data:

.. code-block:: html

    <html>
    <head>
        {{ emit_tep("base_header", extra=dict(a=1, b=True, c=[])) }}
    </head>
    <body>
        {{ emit_tep("base_footer") }}
    </body>
    </html>

