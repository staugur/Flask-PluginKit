.PHONY: clean

help:
	@echo "  clean           remove unwanted stuff"
	@echo "  dev             make a development package"
	@echo "  test            run the tests"
	@echo "  html            use the sphinx-build based on reST build HTML file"
	@echo "  gettext         make gettext"
	@echo "  cn              sphinx-intl update pot for zh_CN"
	@echo "  html-cn         generate the zh_CN translation document"
	@echo "  pipe            make html with en and cn, then clean"

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '.DS_Store' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '.coverage' -exec rm -rf {} +
	rm -rf build dist .eggs *.egg-info +

dev:
	pip install .
	$(MAKE) clean

test:
	python -m unittest
	$(MAKE) clean

html:
	cd docs && sphinx-build -E -T -b html . _build/html

gettext:
	cd docs && sphinx-build -b gettext . _build/gettext 

cn:
	cd docs && sphinx-intl update -p _build/gettext -l zh_CN

html-cn:
	cd docs && sphinx-build -E -T -D language=zh_CN -b html . _build/html_cn

pipe:
	$(MAKE) html
	$(MAKE) gettext
	$(MAKE) cn
	$(MAKE) html-cn
	$(MAKE) clean
