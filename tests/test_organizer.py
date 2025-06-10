import unittest
import os
import shutil
import logging
from datetime import datetime
from unittest.mock import patch, MagicMock
# 修复导入路径
from file_organizer import FileOrganizer

class TestFileOrganizer(unittest.TestCase):
    def setUp(self):
        # 创建临时测试目录
        self.base_dir = os.path.join(os.path.dirname(__file__), 'test_organizer')
        self.source_folder = os.path.join(self.base_dir, 'source')
        self.target_folder = os.path.join(self.base_dir, 'target')
        
        # 创建源文件夹结构
        os.makedirs(self.source_folder, exist_ok=True)
        os.makedirs(os.path.join(self.source_folder, 'subdir'), exist_ok=True)
        
        # 创建测试文件
        self.create_test_file(os.path.join(self.source_folder, 'image1.jpg'), b'image1')
        self.create_test_file(os.path.join(self.source_folder, 'image2.png'), b'image2')
        self.create_test_file(os.path.join(self.source_folder, 'video1.mp4'), b'video1')
        self.create_test_file(os.path.join(self.source_folder, 'subdir', 'image3.jpg'), b'image3')
        self.create_test_file(os.path.join(self.source_folder, 'duplicate.jpg'), b'image1')  # 与image1内容相同
        
        # 初始化整理器
        self.organizer = FileOrganizer(self.source_folder, self.target_folder)
        
        # 禁用日志输出
        logging.disable(logging.CRITICAL)
    
    def tearDown(self):
        # 清理测试目录
        shutil.rmtree(self.base_dir, ignore_errors=True)
        
        # 恢复日志
        logging.disable(logging.NOTSET)
    
    def create_test_file(self, path, content):
        """创建测试文件"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(content)
    
    def test_copy_files(self):
        """测试文件复制功能"""
        self.organizer.copy_files()
        
        # 验证文件是否复制到目标目录
        self.assertTrue(os.path.exists(os.path.join(self.target_folder, 'image1.jpg')))
        self.assertTrue(os.path.exists(os.path.join(self.target_folder, 'image2.png')))
        self.assertTrue(os.path.exists(os.path.join(self.target_folder, 'video1.mp4')))
        self.assertTrue(os.path.exists(os.path.join(self.target_folder, 'image3.jpg')))
        self.assertTrue(os.path.exists(os.path.join(self.target_folder, 'duplicate.jpg')))
    
    def test_deduplicate_files(self):
        """测试去重功能"""
        # 先复制文件
        self.organizer.copy_files()
        
        # 执行去重
        duplicates = self.organizer.deduplicate_files(self.target_folder)
        
        # 验证重复文件已被删除
        self.assertEqual(duplicates, 1)
        self.assertFalse(os.path.exists(os.path.join(self.target_folder, 'duplicate.jpg')))
    
    def test_classify_files(self):
        """测试文件分类功能"""
        # 先复制文件
        self.organizer.copy_files()
        
        # 执行分类
        image_dir, video_dir = self.organizer.classify_files()
        
        # 验证分类结果
        self.assertTrue(os.path.exists(image_dir))
        self.assertTrue(os.path.exists(video_dir))
        self.assertEqual(len(os.listdir(image_dir)), 4)  # 4个图片文件
        self.assertEqual(len(os.listdir(video_dir)), 1)  # 1个视频文件
    
    @patch('file_organizer.get_creation_time')
    def test_process_media_folder(self, mock_get_creation_time):
        """测试媒体文件夹处理功能"""
        # 设置模拟的创建时间
        mock_get_creation_time.return_value = datetime(2023, 6, 10, 12, 30, 45)
        
        # 创建测试媒体文件夹
        test_media_folder = os.path.join(self.target_folder, 'test_media')
        os.makedirs(test_media_folder)
        self.create_test_file(os.path.join(test_media_folder, 'test1.jpg'), b'test1')
        self.create_test_file(os.path.join(test_media_folder, 'test2.jpg'), b'test2')
        
        # 执行处理
        self.organizer.process_media_folder(test_media_folder, 'image')
        
        # 验证文件是否被正确重命名和组织
        camera_dir = os.path.join(test_media_folder, 'camera')
        year_dir = os.path.join(camera_dir, '2023')
        self.assertTrue(os.path.exists(year_dir))
        self.assertEqual(len(os.listdir(year_dir)), 2)
        self.assertTrue(os.path.exists(os.path.join(year_dir, 'IMG_20230610_123045.jpg')))
    
    def test_full_organize(self):
        """测试完整的整理流程"""
        # 执行完整整理
        success = self.organizer.organize()
        
        # 验证整理成功
        self.assertTrue(success)
        
        # 验证最终目录结构
        image_dir = os.path.join(self.target_folder, 'image')
        video_dir = os.path.join(self.target_folder, 'video')
        
        self.assertTrue(os.path.exists(image_dir))
        self.assertTrue(os.path.exists(video_dir))
        
        # 验证图片被正确分类和处理
        image_camera_dir = os.path.join(image_dir, 'camera')
        self.assertTrue(os.path.exists(image_camera_dir))
        
        # 验证视频被正确分类
        self.assertEqual(len(os.listdir(video_dir)), 1)

if __name__ == '__main__':
    unittest.main()
