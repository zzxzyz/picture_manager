import os
import shutil
import unittest

import io
import sys

# 添加父目录到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import merge_all

class TestMergeAll(unittest.TestCase):
    def setUp(self):
        """创建临时源文件夹和目标文件夹"""
        self.source_dir = "test_source"
        self.target_dir = "test_target"
        os.makedirs(self.source_dir, exist_ok=True)
        os.makedirs(self.target_dir, exist_ok=True)
    
    def tearDown(self):
        """清理临时文件夹"""
        shutil.rmtree(self.source_dir, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)
    
    # 测试 1: 基础功能 - 无冲突复制
    def test_basic_copy(self):
        # 创建源文件
        with open(os.path.join(self.source_dir, "file1.txt"), "w") as f:
            f.write("Hello")
        with open(os.path.join(self.source_dir, "file2.txt"), "w") as f:
            f.write("World")
        
        merge_all.copy_files_with_conflict_resolution(self.source_dir, self.target_dir)
        
        # 验证文件数量与内容
        files = os.listdir(self.target_dir)
        self.assertEqual(len(files), 2)
        self.assertIn("file1.txt", files)
        self.assertIn("file2.txt", files)
        with open(os.path.join(self.target_dir, "file1.txt")) as f:
            self.assertEqual(f.read(), "Hello")

    # 测试 2: 源子文件夹文件冲突
    def test_subdirectory_conflict(self):
        # 创建子文件夹及同名文件
        subdir1 = os.path.join(self.source_dir, "sub1")
        subdir2 = os.path.join(self.source_dir, "sub2")
        os.makedirs(subdir1)
        os.makedirs(subdir2)
        
        # 不同内容的同名文件
        with open(os.path.join(subdir1, "conflict.txt"), "w") as f:
            f.write("First")
        with open(os.path.join(subdir2, "conflict.txt"), "w") as f:
            f.write("Second")
        
        merge_all.copy_files_with_conflict_resolution(self.source_dir, self.target_dir)
        
        # 验证重命名结果
        files = os.listdir(self.target_dir)
        self.assertEqual(len(files), 2)
        self.assertIn("conflict.txt", files)
        self.assertIn("conflict_1.txt", files)
        # 检查内容完整性
        contents = set()
        for file in files:
            with open(os.path.join(self.target_dir, file)) as f:
                contents.add(f.read())
        self.assertEqual(contents, {"First", "Second"})

    # 测试 3: 目标文件夹已有同名文件
    def test_existing_target_conflict(self):
        # 在目标文件夹预创建文件
        with open(os.path.join(self.target_dir, "existing.txt"), "w") as f:
            f.write("Old")
        # 在源文件夹创建同名文件
        with open(os.path.join(self.source_dir, "existing.txt"), "w") as f:
            f.write("New")
        
        merge_all.copy_files_with_conflict_resolution(self.source_dir, self.target_dir)
        
        # 验证重命名
        files = os.listdir(self.target_dir)
        self.assertEqual(len(files), 2)
        self.assertIn("existing.txt", files)  # 原始文件
        self.assertIn("existing_1.txt", files)  # 新复制文件
        with open(os.path.join(self.target_dir, "existing_1.txt")) as f:
            self.assertEqual(f.read(), "New")

    # 测试 4: 空源文件夹
    def test_empty_source(self):
        merge_all.copy_files_with_conflict_resolution(self.source_dir, self.target_dir)
        self.assertEqual(len(os.listdir(self.target_dir)), 0)  # 目标应为空

    # 测试 5: 源文件夹不存在
    def test_source_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            merge_all.copy_files_with_conflict_resolution("non_existent_folder", self.target_dir)

    # 测试 6: 目标文件夹自动创建
    def test_target_auto_create(self):
        shutil.rmtree(self.target_dir)  # 确保目标不存在
        with open(os.path.join(self.source_dir, "test.txt"), "w") as f:
            f.write("Test")
        
        merge_all.copy_files_with_conflict_resolution(self.source_dir, self.target_dir)
        self.assertTrue(os.path.exists(self.target_dir))  # 目标应被创建
        self.assertIn("test.txt", os.listdir(self.target_dir))

    # 测试 7: 特殊文件名（空格/中文/特殊符号）
    def test_special_filenames(self):
        special_names = [
            "file with spaces.txt",
            "中文文件.txt",
            "file!@#$.bin"
        ]
        for name in special_names:
            with open(os.path.join(self.source_dir, name), "w") as f:
                f.write(name)
        
        merge_all.copy_files_with_conflict_resolution(self.source_dir, self.target_dir)
        
        # 验证文件名和内容完整性
        for name in special_names:
            self.assertIn(name, os.listdir(self.target_dir))
            with open(os.path.join(self.target_dir, name)) as f:
                self.assertEqual(f.read(), name)

    # 测试 8: 大量文件冲突
    def test_massive_conflicts(self):
        # 创建 10 个同名文件
        for i in range(10):
            subdir = os.path.join(self.source_dir, f"dir_{i}")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "massive.txt"), "w") as f:
                f.write(f"Content {i}")
        
        merge_all.copy_files_with_conflict_resolution(self.source_dir, self.target_dir)
        
        # 验证生成文件：massive.txt, massive_1.txt, ..., massive_9.txt
        files = os.listdir(self.target_dir)
        self.assertEqual(len(files), 10)
        for i in range(10):
            expected = f"massive_{i}.txt" if i > 0 else "massive.txt"
            self.assertIn(expected, files)

if __name__ == "__main__":
    unittest.main()
