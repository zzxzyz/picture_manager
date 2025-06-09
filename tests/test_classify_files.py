import os
import sys
import unittest
import shutil
import tempfile

# 添加父目录到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import classify_files

class TestClassifyFiles(unittest.TestCase):
    def setUp(self):
        # 创建临时测试目录
        # 打印当前测试名称
        print(f"\n=== 开始测试: {self._testMethodName} ===")
        self.test_dir = tempfile.mkdtemp()
        print(f"\n=== 测试目录: {self.test_dir} ===")
        
    def tearDown(self):
        # 清理测试目录
        shutil.rmtree(self.test_dir)
    
    def create_test_file(self, filename, content=None):
        """创建测试文件"""
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, "w") as f:
            f.write(content or "test content")
        return filepath
    
    def test_empty_directory(self):
        """测试空目录"""
        classify_files.classify_files(self.test_dir)
        
        # 验证目录结构
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'image')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'video')))
        self.assertEqual(len(os.listdir(self.test_dir)), 2)  # 只有两个目录
    
    def test_file_classification(self):
        """测试文件分类"""
        # 创建测试文件
        img1 = self.create_test_file("photo1.jpg")
        img2 = self.create_test_file("photo2.PNG")
        vid1 = self.create_test_file("movie1.mp4")
        vid2 = self.create_test_file("movie2.MOV")
        other1 = self.create_test_file("document.pdf")
        other2 = self.create_test_file("data.txt")
        
        classify_files.classify_files(self.test_dir)
        
        # 验证文件位置
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'image', "photo1.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'image', "photo2.PNG")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'video', "movie1.mp4")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'video', "movie2.MOV")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "document.pdf")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "data.txt")))
    
    def test_existing_directories(self):
        """测试目标目录已存在"""
        # 预先创建目录
        os.makedirs(os.path.join(self.test_dir, 'image'), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'video'), exist_ok=True)
        
        # 创建测试文件
        img = self.create_test_file("photo.jpg")
        
        classify_files.classify_files(self.test_dir)
        
        # 验证文件被移动
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'image', "photo.jpg")))
    
    def test_edge_cases(self):
        """测试边界条件"""
        # 创建特殊文件
        no_ext = self.create_test_file("no_extension")
        hidden = self.create_test_file(".hidden_file")
        long_name = self.create_test_file("a" * 200 + ".png")
        
        classify_files.classify_files(self.test_dir)
        
        # 验证特殊文件处理
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "no_extension")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".hidden_file")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'image', "a" * 200 + ".png")))

if __name__ == "__main__":
    unittest.main()
