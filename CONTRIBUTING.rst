
Thank you for considering contributing to Flask-PluginKit!

问题反馈
------------

* The `issues <https://github.com/staugur/Flask-PluginKit/issues>`_ on GitHub.
* The email for staugur@saintic.com

报告问题
------------

- 描述你预期会发生什么。
- 如果可能，请包含一个最小的、完整的、可验证的示例，以帮助我们识别问题。这还有助于检查问题是否与您自己的代码无关。
- 描述实际发生了什么。如果有异常，包括完整的异常堆栈。
- 列出您的Python、Flask、Flask-PluginKit版本。如果可能，检查新版本是否已经修复了这个问题。

提交pr
----------

**首先是环境**


* fork仓库 `Flask-PluginKit <https://github.com/staugur/Flask-PluginKit>`_
* git克隆您账号下的Flask-PluginKit，并设置好您的 `git config`
* 安装开发环境的依赖模块 `pip install -r dev-requirements.txt`

**其次是编码**

* 编写代码，请尽量符合PEP8规范。
* 编写测试用例和文档。
* 分别使用pypy、py2.7、py3.4+环境运行测试 `make dev && make test` 。
* 使用py3.4+环境可以生成文档 `make dev && make html` ，如果您贡献翻译文档，请再执行命令 `make en` ，然后翻译po文件，最后执行 `make trans` 生成翻译文档。

**最后请求合并**

* 提交你的代码
* 在GitHub上发起 `pull request`
