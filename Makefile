.PHONY: clean

help:
	@echo "  clean           remove unwanted stuff"
	@echo "  dev             make a development package"
	@echo "  test            run the tests"
	@echo "  publish-test    package and upload a release to test.pypi.org"
	@echo "  publish-release package and upload a release to pypi.org"
	@echo "  init-docs       use the sphinx-quickstart initialization document catalogue quickly"
	@echo "  rst             use the sphinx-apidoc extract documentation from code comments"
	@echo "  html            use the sphinx-build based on reST build HTML file"

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '.DS_Store' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '.coverage' -exec rm -rf {} +
	rm -rf build dist *.egg-info +

dev:
	pip uninstall Flask-PluginKit -y
	pip install .
	$(MAKE) clean

test:
	python setup.py test
	$(MAKE) clean

publish-test:
	python setup.py publish --test

publish-release:
	python setup.py publish --release

init-docs:
	sphinx-quickstart -q -p Flask-PluginKit -a staugur --ext-autodoc --ext-viewcode --no-makefile --no-batchfile docs

rst:
	$(MAKE) dev
	sphinx-apidoc -d 2 -f --ext-autodoc --ext-viewcode --private -o docs flask_pluginkit

html:
	sphinx-build -b html docs docs/_build/html
