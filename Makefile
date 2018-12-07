.PHONY: clean

help:
	@echo "  clean           remove unwanted stuff"
	@echo "  dev             make a development package"
	@echo "  test            run the tests"
	@echo "  publish-test    package and upload a release to test.pypi.org"
	@echo "  publish-release package and upload a release to pypi.org"
	@echo "  rst             use the sphinx-apidoc extract documentation from code comments"
	@echo "  html            use the sphinx-build based on reST build HTML file"
	@echo "  gettext         make gettext"
	@echo "  en              sphinx-intl update pot for en"
	@echo "  trans           start to translate"
	@echo "  pipe            make html and gettext -> en -> trans, then clean"

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '.DS_Store' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '.coverage' -exec rm -rf {} +
	rm -rf build dist *.egg-info +

dev:
	pip install .
	$(MAKE) clean

test:
	python setup.py test
	$(MAKE) clean

publish-test:
	python setup.py publish --test

publish-release:
	python setup.py publish --release

rst:
	$(MAKE) dev
	sphinx-apidoc -d 2 -f --ext-autodoc --ext-viewcode --private -o docs flask_pluginkit

html:
	cd docs && sphinx-build -b html . _build/html

gettext:
	cd docs && sphinx-build -b gettext . _build/locale

en:
	cd docs && sphinx-intl update -p _build/locale/ -l en

trans:
	cd docs && sphinx-build -D language=en -b html . _build/html_en

pipe:
	$(MAKE) html
	$(MAKE) gettext
	$(MAKE) en
	$(MAKE) trans
	$(MAKE) clean
