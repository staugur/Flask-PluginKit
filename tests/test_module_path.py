import unittest
import sys
import os
import tempfile
import shutil
import importlib

# 假设 get_module_path 函数在 module_utils 模块中
from flask_pluginkit.utils import get_module_path
from os.path import abspath


class TestGetModulePath(unittest.TestCase):
    """测试 get_module_path 函数的基础场景"""
    
    def setUp(self):
        """每个测试前的准备工作"""
        # 保存原始的 sys.path
        self.original_sys_path = sys.path.copy()
        
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp(prefix="test_modules_")
        
        # 创建测试模块
        self.create_test_modules()
        
        # 添加测试目录到 Python 路径
        sys.path.insert(0, self.test_dir)
    
    def tearDown(self):
        """每个测试后的清理工作"""
        # 恢复 sys.path
        sys.path = self.original_sys_path
        
        # 删除临时目录
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # 清理 sys.modules 中的测试模块
        for module_name in list(sys.modules.keys()):
            if module_name.startswith("test_"):
                del sys.modules[module_name]
    
    def create_test_modules(self):
        """创建简单的测试模块结构"""
        # 创建普通测试模块
        module_file = os.path.join(self.test_dir, "test_module.py")
        with open(module_file, "w") as f:
            f.write("value = 42")
        
        # 创建测试包
        package_dir = os.path.join(self.test_dir, "test_package")
        os.makedirs(package_dir, exist_ok=True)
        
        # 包初始化文件
        init_file = os.path.join(package_dir, "__init__.py")
        with open(init_file, "w") as f:
            f.write("version = '1.0'")
    
    def test_existing_module(self):
        """测试存在的模块"""
        # 测试标准库模块
        path = get_module_path("os")
        
        # 验证返回结果
        self.assertIsNotNone(path)
        self.assertTrue(os.path.isabs(path))
        self.assertTrue(path.endswith(".py") or ".so" in path or ".pyd" in path)
    
    def test_module_from_file(self):
        """测试从文件导入的模块"""
        path = get_module_path("test_module")
        
        # 验证返回结果
        self.assertIsNotNone(path)
        self.assertTrue(os.path.isabs(path))
        self.assertTrue(path.endswith("test_module.py"))
        self.assertTrue(os.path.exists(path))
    
    def test_package(self):
        """测试包"""
        path = get_module_path("test_package")
        
        # 验证返回结果
        self.assertIsNotNone(path)
        self.assertTrue(os.path.isabs(path))
        
        # 包路径应该包含 __init__.py
        self.assertTrue(os.path.exists(path))
    
    def test_non_existing_module(self):
        """测试不存在的模块"""
        path = get_module_path("non_existing_module_xyz123")
        
        # 应该返回 None
        self.assertIsNone(path)
    
    def test_builtin_module(self):
        """测试内置模块"""
        # 找一个真正的内置模块
        for module_name in sys.builtin_module_names:
            if module_name.startswith("_"):  # 如 "_ast"
                path = get_module_path(module_name)
                
                # 内置模块没有 __file__ 和 __path__，应该返回 None
                self.assertIsNone(path)
                break
    
    def test_submodule(self):
        """测试子模块"""
        # 测试标准库子模块
        path = get_module_path("os.path")
        
        # 验证返回结果
        self.assertIsNotNone(path)
        self.assertTrue(os.path.isabs(path))


if __name__ == '__main__':
    # 运行测试
    unittest.main()