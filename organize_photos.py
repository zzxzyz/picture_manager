#!/usr/bin/env python3
"""
照片整理工具
功能：
1. 读取照片拍摄时间并分类到camera/photo目录
2. 重命名照片为IMG_日期_时间格式
3. 按年份分组照片
"""

import argparse
import logging
import sys
import os
import os.path
from PIL import Image, ExifTags
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('photo_organizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_exif_datetime(image_path):
    """
    获取照片的拍摄时间
    返回格式: YYYY:MM:DD HH:MM:SS 或 None
    """
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()
            if exif:
                for tag, value in exif.items():
                    if ExifTags.TAGS.get(tag) == 'DateTimeOriginal':
                        # 处理异常时间格式
                        clean_value = value.split('.')[0]  # 移除毫秒部分
                        clean_value = clean_value[:19]  # 确保长度正确
                        return clean_value
    except Exception as e:
        logger.error(f"读取 {image_path} EXIF 失败: {str(e)}")
    return None


def create_target_filename(dt_str, ext, existing_files):
    """
    创建目标文件名并解决冲突
    """
    try:
        dt_obj = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        base_name = f"IMG_{dt_obj.strftime('%Y%m%d_%H%M%S')}"
        target_name = f"{base_name}{ext}"
        
        # 解决文件名冲突
        counter = 1
        while target_name in existing_files:
            target_name = f"{base_name}_{counter}{ext}"
            counter += 1
            
        return target_name
    except ValueError:
        logger.error(f"无效的日期时间格式: {dt_str}")
        return None


def classify_photos(source_path, camera_dir, photo_dir):
    """
    步骤1: 分类照片到camera和photo目录
    """
    logger.info(f"开始分类照片: {source_path}")
    
    # 获取所有文件
    all_files = os.listdir(source_path)
    image_exts = ['.jpg', '.jpeg', '.png', '.cr2', '.nef']
    
    for filename in all_files:
        file_path = os.path.join(source_path, filename)
        if not os.path.isfile(file_path):
            continue
            
        _, ext = os.path.splitext(filename)
        if ext.lower() in image_exts:
            dt_str = get_exif_datetime(file_path)
            if dt_str:
                logger.info(f"{filename} - 拍摄时间: {dt_str}")
                target_path = os.path.join(camera_dir, filename)
                os.rename(file_path, target_path)
            else:
                logger.info(f"{filename} - 无拍摄时间")
                target_path = os.path.join(photo_dir, filename)
                os.rename(file_path, target_path)
    
    camera_count = len(os.listdir(camera_dir))
    photo_count = len(os.listdir(photo_dir))
    logger.info(f"照片分类完成! camera: {camera_count}张, photo: {photo_count}张")


def rename_photos(camera_dir):
    """
    步骤3: 重命名照片文件
    """
    logger.info(f"开始重命名照片: {camera_dir}")
    
    camera_files = os.listdir(camera_dir)
    existing_names = camera_files.copy()
    renamed_count = 0
    skipped_count = 0
    
    for filename in camera_files:
        file_path = os.path.join(camera_dir, filename)
        if not os.path.isfile(file_path):
            continue
            
        dt_str = get_exif_datetime(file_path)
        if not dt_str:
            continue
            
        _, ext = os.path.splitext(filename)
        # 检查是否需要重命名
        new_name = create_target_filename(dt_str, ext, existing_names)
        if not new_name:
            continue
            
        if filename != new_name:
            logger.info(f"重命名: {filename} -> {new_name}")
            new_path = os.path.join(camera_dir, new_name)
            os.rename(file_path, new_path)
            existing_names.remove(filename)
            existing_names.append(new_name)
            renamed_count += 1
        else:
            logger.info(f"跳过重命名: {filename} 已符合命名规则")
            skipped_count += 1
    
    logger.info(f"重命名完成! 已重命名: {renamed_count}张, 跳过: {skipped_count}张")


def group_by_year(camera_dir):
    """
    步骤4: 按年份分组照片
    """
    logger.info(f"开始按年份分组照片: {camera_dir}")
    
    moved_count = 0
    for filename in os.listdir(camera_dir):
        file_path = os.path.join(camera_dir, filename)
        if not os.path.isfile(file_path):
            continue
            
        if filename.startswith("IMG_") and len(filename) >= 12:
            year = filename[4:8]  # 从 IMG_YYYYMMDD... 提取年份
            if year.isdigit():
                year_dir = os.path.join(camera_dir, year)
                if not os.path.exists(year_dir):
                    os.makedirs(year_dir)
                target_path = os.path.join(year_dir, filename)
                logger.info(f"移动 {filename} -> {year}/")
                os.rename(file_path, target_path)
                moved_count += 1
    
    logger.info(f"年份分组完成! 已移动: {moved_count}张照片")


def main():
    parser = argparse.ArgumentParser(description='整理照片工具')
    parser.add_argument('source_dir', type=str, help='源目录路径')
    args = parser.parse_args()
    
    source_path = os.path.abspath(args.source_dir)
    if not os.path.isdir(source_path):
        logger.error(f"目录不存在: {source_path}")
        sys.exit(1)
    
    # 创建分类目录
    camera_dir = os.path.join(source_path, "camera")
    photo_dir = os.path.join(source_path, "photo")
    
    if not os.path.exists(camera_dir):
        os.makedirs(camera_dir)
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)
    
    # 执行处理步骤
    classify_photos(source_path, camera_dir, photo_dir)  # 步骤1
    
    # 步骤2: 进入camera目录
    os.chdir(camera_dir)
    logger.info(f"当前工作目录: {camera_dir}")
    
    rename_photos(camera_dir)  # 步骤3
    group_by_year(camera_dir)  # 步骤4
    
    logger.info("照片整理完成!")


if __name__ == "__main__":
    main()
