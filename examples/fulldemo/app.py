# -*- coding: utf-8 -*-

from flask import Flask, render_template_string
from flask_pluginkit import PluginManager

app = Flask(__name__)
pm = PluginManager(
    app,
    plugin_packages=['flask_pluginkit_demo'],
    pluginkit_config=dict(whoami='localdemo_config')
)


@app.route('/')
def index():
    return render_template_string("""\
<html>
<head>
    {{ emit_assets('localdemo','css/style.css') }}
</head>
<body>

    {{ emit_tep('code') }}
    {{ emit_tep('html') }}

    <div id='demo'></div>

    {{ emit_assets('localdemo','js/hello.js') }}
    {{ emit_config('whoami') }}

</body>
</html>""")


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
