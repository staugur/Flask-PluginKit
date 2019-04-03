#!/bin/bash
set -e

echo "Flask-PluginKit演示用例：包含本地和第三方pypi插件"

dir=$(cd $(dirname $0); pwd)

echo ">>> 安装测试插件"
cd ${dir}/pypi
pip install .

echo ">>> 运行Web进程"
cd ${dir}
export FLASK_ENV=development && python main.py
