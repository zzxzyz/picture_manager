import unittest
import os
import shutil
from datetime import datetime
from unittest.mock import patch
# 修复导入路径
from utils import calculate_md5, get_creation_time, safe_copy, format_time

class TestUtils(unittest.TestCase):
    def setUp(self):
        # 创建临时测试目录
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # 创建测试文件
        self.test_file = os.path.join(self.test_dir, 'test.txt')
        with open(self.test_file, 'w') as f:
            f.write('Hello, World!')
    
    def tearDown(self):
        # 清理测试目录
        shutil.rmtree(self.test_dir)
    
    def test_calculate_md5(self):
        """测试MD5计算功能"""
        md5 = calculate_md5(self.test_file)
        self.assertEqual(md5, '65a8e27d8879283831b664bd8b7f0ad4')
    
    @patch('os.path.getmtime')
    def test_get_creation_time(self, mock_getmtime):
        """测试获取创建时间功能"""
        # 设置模拟的修改时间
        mock_getmtime.return_value = 1672531200  # 2023-01-01 00:00:00
        
        # 测试获取时间
        time = get_creation_time(self.test_file)
        self.assertEqual(time, datetime(2023, 1, 1))
    
    def test_safe_copy(self):
        """测试安全复制功能"""
        # 创建目标目录
        target_dir = os.path.join(self.test_dir, 'target')
        os.makedirs(target_dir, exist_ok=True)
        
        # 第一次复制
        copy1 = safe_copy(self.test_file, target_dir)
        self.assertTrue(os.path.exists(copy1))
        
        # 第二次复制同名文件
        copy2 = safe_copy(self.test_file, target_dir)
        self.assertTrue(os.path.exists(copy2))
        self.assertNotEqual(copy1, copy2)
    
    def test_format_time(self):
        """测试时间格式化功能"""
        dt = datetime(2023, 1, 1, 12, 30, 45)
        self.assertEqual(format_time(dt, '%Y%m%d_%H%M%S'), '20230101_123045')
        self.assertEqual(format_time(dt, '%Y:%m:%d %H:%M:%S'), '2023:01:01 12:30:45')

if __name__ == '__main__':
    unittest.main()
