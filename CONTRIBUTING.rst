How to contribute to Flask-PluginKit
====================================

Thank you for considering contributing to Flask-PluginKit!

Feedback
--------

* The `issues <https://github.com/staugur/Flask-PluginKit/issues>`_ on GitHub.

Report a problem
----------------

- Describe what you expect to happen.

- If possible, include a minimal, complete, verifiable example to
  help us identify the problem. This also helps to check if the issue
  is not related to your own code.

- Describe what actually happened. If there is an exception,
  include the complete exception stack.

- List your Python, Flask, Flask-PluginKit versions.
  If possible, check if the new version has fixed this issue.

Submit pull request
-------------------

**First is the environment**

* fork repository `Flask-PluginKit <https://github.com/staugur/Flask-PluginKit>`_

* git clone Flask-PluginKit under your account and set your `git config`

* Install the dependency module of the development environment
  with command ``make dev``

**Followed by coding**

* Write code, please try to comply with the PEP8 specification.

* Write test cases and documentation.

* Run the test ``make dev && make test`` using the py3.8+ environments respectively.

* Generate the documentation ``make dev && make html``.

* If you contribute a translation document, proceed as follows:

  1. execute the command ``make gettext``

    Extract translatable messages into pot files. The generated pot file
    will be placed in the docs/_build/gettext directory.

  2. execute the command ``make cn``

    Generate or update the po file and place it in
    ``docs/locale/zh_CN/LC_MESSAGES/`` directory, then translate the po file.

  3. execute the command ``make html-cn``

    Constructing Translation Documents, at the same time, it will generate
    or update mo file.

**Last request for merger**

* Submit your code

* Initiate ``pull request`` on GitHub
