# -*- coding: utf-8 -*-
"""
    Flask-PluginKit
    ~~~~~~~~~~~~~~~

    utils: Some gadgets.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    try:
        user = models.User.objects.get(username=username)
    except models.User.DoesNotExist:
        user = None

    if user and user.verify_password(password):
        return True

    return False


def not_authenticated():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return not_authenticated()
        return f(*args, **kwargs)
    return decorated
