import os
import sys
import unittest
import shutil
import tempfile
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, IFD
import piexif

# 添加父目录到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import organize_photos

class TestOrganizePhotos(unittest.TestCase):
    def setUp(self):
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp()
        print(f"\n=== 测试目录: {self.test_dir} ===")
        
    def tearDown(self):
        # 清理测试目录
        shutil.rmtree(self.test_dir)
    
    def create_test_image(self, filename, shooting_time=None):
        """创建测试图片，可选添加EXIF拍摄时间"""
        filepath = os.path.join(self.test_dir, filename)
        
        # 创建空白图片
        img = Image.new('RGB', (100, 100), color='red')
        img.save(filepath)
        
        # 添加EXIF数据
        if shooting_time:
            exif_dict = {
                "0th": {},
                "Exif": {},
                "GPS": {},
                "1st": {},
                "thumbnail": None
            }
            
            # 设置拍摄时间
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = shooting_time
            
            # 保存EXIF数据
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, filepath)
        
        return filepath
    
    def test_get_shooting_time_normal(self):
        """测试正常拍摄时间获取"""
        # 创建测试图片
        img_path = self.create_test_image("normal.jpg", "2023:05:15 14:30:00")
        
        # 获取拍摄时间
        shooting_time = organize_photos.get_shooting_time(img_path)
        self.assertIsNotNone(shooting_time)
        self.assertEqual(shooting_time.strftime("%Y:%m:%d %H:%M:%S"), "2023:05:15 14:30:00")
    
    def test_get_shooting_time_abnormal(self):
        """测试异常拍摄时间格式"""
        # 创建测试图片
        img_path = self.create_test_image("abnormal.jpg", "2023:05:15 14:30:00aa")
        
        # 获取拍摄时间
        shooting_time = organize_photos.get_shooting_time(img_path)
        self.assertIsNotNone(shooting_time)
        self.assertEqual(shooting_time.strftime("%Y:%m:%d %H:%M:%S"), "2023:05:15 14:30:00")
    
    def test_classification(self):
        """测试照片分类"""
        # 创建测试图片
        with_time = self.create_test_image("with_time.jpg", "2023:05:15 14:30:00")
        without_time = self.create_test_image("without_time.jpg")
        
        # 处理照片
        organize_photos.process_photos(self.test_dir)
        
        # 验证分类
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'camera', '2023', 'IMG_20230515_143000.jpg')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'photo', 'without_time.jpg')))
    
    def test_rename_conflict(self):
        """测试文件名冲突处理"""
        # 创建两个相同时间的图片
        img1 = self.create_test_image("img1.jpg", "2023:05:15 14:30:00")
        img2 = self.create_test_image("img2.jpg", "2023:05:15 14:30:00")
        
        # 处理照片
        organize_photos.process_photos(self.test_dir)
        
        # 验证重命名
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'camera', '2023', 'IMG_20230515_143000.jpg')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'camera', '2023', 'IMG_20230515_143000_1.jpg')))
    
    def test_skip_renaming(self):
        """测试跳过已正确命名的文件"""
        # 创建已正确命名的图片
        img_path = self.create_test_image("IMG_20230515_143000.jpg", "2023:05:15 14:30:00")
        
        # 处理照片
        organize_photos.process_photos(self.test_dir)
        
        # 验证文件位置（应直接移动到年份目录）
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'camera', '2023', 'IMG_20230515_143000.jpg')))
    
    def test_year_grouping(self):
        """测试按年份分组"""
        # 创建不同年份的图片
        img2022 = self.create_test_image("2022.jpg", "2022:01:01 00:00:00")
        img2023 = self.create_test_image("2023.jpg", "2023:01:01 00:00:00")
        
        # 处理照片
        organize_photos.process_photos(self.test_dir)
        
        # 验证分组
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'camera', '2022', 'IMG_20220101_000000.jpg')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'camera', '2023', 'IMG_20230101_000000.jpg')))

if __name__ == "__main__":
    unittest.main()
