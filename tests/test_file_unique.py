import argparse
import os
import sys
import unittest
import shutil
import hashlib
import io

# 添加父目录到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import file_unique
from unittest.mock import patch, MagicMock

class TestFileUnique(unittest.TestCase):
    def setUp(self):
        # 打印当前测试名称
        print(f"\n=== 开始测试: {self._testMethodName} ===")
        
        # 创建临时测试目录
        self.test_dir = "test_dir"
        os.makedirs(self.test_dir, exist_ok=True)
    
    def tearDown(self):
        # 清理测试目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_test_file(self, filename, content=None):
        """创建测试文件"""
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, "w") as f:
            f.write(content or os.urandom(16).hex())
        return filepath
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_empty_directory(self, mock_stdout):
        """测试空目录"""
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(directory=self.test_dir, simulate=False)
            file_unique.main()
        output = mock_stdout.getvalue()
        self.assertIn("✅ 未发现重复文件", output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_no_duplicates(self, mock_stdout):
        """测试无重复文件"""
        self.create_test_file("file1.txt")
        self.create_test_file("file2.txt")
        
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(directory=self.test_dir, simulate=False)
            file_unique.main()
        output = mock_stdout.getvalue()
        self.assertIn("✅ 未发现重复文件", output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_duplicate_files(self, mock_stdout):
        """测试重复文件删除"""
        content = "same content"
        file1 = self.create_test_file("file1.txt", content)
        file2 = self.create_test_file("file2.txt", content)
        file3 = self.create_test_file("file3.txt", content)
        
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(directory=self.test_dir, simulate=False)
            file_unique.main()
        
        # 验证只保留了第一个文件
        self.assertTrue(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))
        self.assertFalse(os.path.exists(file3))
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_simulate_mode(self, mock_stdout):
        """测试模拟运行模式"""
        content = "same content"
        file1 = self.create_test_file("file1.txt", content)
        file2 = self.create_test_file("file2.txt", content)
        
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(directory=self.test_dir, simulate=True)
            file_unique.main()
        output = mock_stdout.getvalue()
        
        # 验证文件未被删除
        self.assertTrue(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))
        self.assertIn("[SIMULATE]", output)
    
    # @patch('sys.stdout', new_callable=io.StringIO)
    # def test_unreadable_file(self, mock_stdout):
    #     """测试无法读取的文件"""
    #     file1 = self.create_test_file("file1.txt")
    #     file2 = self.create_test_file("file2.txt")
        
    #     # 使第二个文件不可读
    #     os.chmod(file2, 0o000)
        
    #     with patch("argparse.ArgumentParser.parse_args") as mock_args:
    #         mock_args.return_value = MagicMock(directory=self.test_dir, simulate=False)
    #         file_unique.main()
    #     output = mock_stdout.getvalue()
        
    #     # 验证有错误日志
    #     self.assertIn("删除失败", output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_large_file_handling(self, mock_stdout):
        """测试大文件处理能力"""
        # 创建100MB大文件
        large_content = os.urandom(100 * 1024 * 1024)
        file1 = self.create_test_file("large1.bin", large_content.hex())
        file2 = self.create_test_file("large2.bin", large_content.hex())
        
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(directory=self.test_dir, simulate=False)
            file_unique.main()
        
        # 验证重复文件被正确处理
        self.assertTrue(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))

if __name__ == "__main__":
    unittest.main()
