.. _vep:

View function Extension Point
=============================

Description
-----------

The extension point abbreviation is vep.

Vep is a simple way for plugins to directly add routing functions,
because in previous versions, routing was only allowed through blueprints.

The plugin needs to return the vep field via register. The returned vep
data type can be dict, list, tuple.

The dict format is {rule:, view_func:}, which means that a single route
is added. The dict content is the parameter of
:meth:`~flask.Flask.add_url_rule`, reference document `add_url_rule`_,
a common example is:

.. code-block:: python

    def vep():
        return "vep"

    dict(rule="/vep", view_func=vep, endpoint="vep", methods=["GET", "POST"])

Other types are represented as multiple routes,
and multiple dict data of the above type can be nested.

The Flask-PluginKit loads vep via
:meth:`~flask_pluginkit.PluginManager._vep_handler`, this method will
detect vep rules and specific content.

.. _add_url_rule: http://flask.palletsprojects.com/api/#flask.Flask.add_url_rule

.. _vep-on-blueprint:

vep on blueprint
----------------

The vep allows to be set on the blueprint, format: {_blueprint: blueprint-name, rule:/path, view_func:xx}.

Require blueprint to exist, otherwise raise :class:`~flask_pluginkit.exceptions.PEPError`

.. versionadded:: 3.6.0

Example
-------

- Plugin registration for vep

.. code-block:: python

    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    def upload_file():
        if request.method == 'POST':
            # save post file
            return redirect(url_for('uploaded_file', filename=filename))
        else:
            return '''
            <form method=post enctype=multipart/form-data>
                <input type=file name=file>
                <input type=submit value=Upload>
            </form>
            '''

    def bvep():
        return "vep on blueprint"

    def register():
        return dict(
            vep = [
                dict(
                    rule="/uploads/<filename>",
                    view_func=uploaded_file
                ),
                dict(
                    rule="/upload",
                    view_func=upload_file,
                    methods=["GET", "POST"]
                ),
                # Suppose a blueprint named test,
                # and the endpoint will be test.bvep(endpoint set it)
                dict(
                    _blueprint="test",
                    rule="/vep-on-blueprint",
                    view_func=bvep,
                )
            ]
        )

- User Access

Access /upload display form, access the uploaded file via /uploads/filename.
