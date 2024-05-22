.. currentmodule:: flask-pluginkit

v3.8.0
------

Released in 2024-05-23

Only support python 3.8+ and flask 3.0+


v3.7.2
------

Released in 2023-05-17

- Fixed semver version
- Drop hep `before_first_request`

v3.7.1
------

Released in 2021-09-07

Restore translations.ini

v3.7.0
------

Released in 2021-09-02

- feat: add :ref:`p3`, is beta
- chore: the stpl_reverse falls into stpl
- deprecated: will remove the try_compatible and stpl_reverse in :class:`~flask_pluginkit.PluginManager`
- misc: remove web static files(change to CDN)

v3.6.2
------

Released in 2021-06-22

- chore: compatible with flask 2.0 nested blueprints, but only supports blueprints of nested plugins
- fix ci(deploy pypi) & update docs

v3.6.1
------

Released in 2021-06-22

- ci tests from travis to github action
- chore: web message api with SSE, page with CDN

v3.6.0
------

Released in 2020-12-31

- feat: add :ref:`vep-on-blueprint`, is beta
- feat: the :meth:`~flask_pluginkit.PluginManager.emit_assets` add _external
- fix: semver.compare and semver.parse
- update docs & test case, example
- deprecated: MongoStorage

v3.5.0
------

Released in 2020-04-08

- feat: add class-based view extension point (beta, use Flask-Classful) 
- chore: web plugin manager page setInterval (called as needed)
- update docs & test case, example

v3.4.1
------

Released in 2020-03-25

- feat: add :meth:`~flask_pluginkit.LocalStorage.setmany`
- feat: add :meth:`~flask_pluginkit.RedisStorage.setmany`
- fix: update result(original) :meth:`~flask_pluginkit.RedisStorage.get`

v3.4.0
------

Released in 2019-09-27

- feat: add before_first_request hook to hep
- feat: errhandler allow exception
- feat: emit_assets add _raw param
- feat: filter allow [f1, f2, (name, f3)]
- feat: web manager add a button, select language
- feat: stpl alow asc or desc, open the template sorting
- fix: check getPluginClass
- fix: check url prefix
- chore: update docs, example and test case

v3.3.1
------

Released in 2019-09-17

- feat: automatically compatible 2.x partial registration method
- fix: update shelve set key type
- fix: remove the number of tests `/`
- test: add docs
- chore: update travis.yml
- chore: formatting code and optimizing import

v3.3.0
------

Released in 2019-07-31

- feat: update :class:`~flask_pluginkit.PluginInstaller`.
- feat: add a blueprint to manage plugins
- fix: close shelve connection
- test: add test case
- docs: update docs and translation
- chore: update example
- chore: update travis.yml, add deploy

v3.2.0
------

Released in 2019-07-25

- feat: dcp, be similar to flask-plugins event system,
        add :class:`~flask_pluginkit.utils.DcpManager`
        and :func:`~flask_pluginkit.push_dcp`
- feat: add error handler
- feat: add template filter
- feat: add template context processor
- test: add test case
- docs: update docs and translation
- chore: update example
- chore: make some of the code more elegant

v3.1.0
------

Released in 2019-07-22

- feat: add :class:`~flask_pluginkit.PluginInstaller`
- feat: add vep :ref:`vep`
- test: add test case
- docs: update docs
- chore: update example

v3.0.1
------

Released in 2019-07-21

- The register functin can return empty dict, not necessarily meaningless.
- Update docs, translation and add test.

v3.0.0
------

Released in 2019-07-20

- Refactoring everyting

Previous Versions
-----------------

Prior to 3.3.1, the new version of the refactoring was not compatible
with the old version, and the update history is no longer recorded here.
