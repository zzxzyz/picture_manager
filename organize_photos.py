#!/usr/bin/env python3
"""
照片整理工具
主程序入口
"""

import argparse
import logging
import sys
import os
import re
from collections import defaultdict
import file_utils
import media_utils
import duplicate_utils
from datetime import datetime

# 确保logs目录存在
os.makedirs('logs', exist_ok=True)
    
# 配置日志
current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = os.path.join('logs', f'media_{current_time}.log')
    
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 使用新模块中的函数
copy_files_with_conflict_resolution = file_utils.copy_files_with_conflict_resolution
generate_conflict_report = file_utils.generate_conflict_report
move_file_with_conflict_resolution = file_utils.move_file_with_conflict_resolution
calculate_md5 = duplicate_utils.calculate_md5
find_duplicate_files = duplicate_utils.find_duplicate_files
delete_duplicates = duplicate_utils.delete_duplicates
find_and_delete_duplicates = duplicate_utils.find_and_delete_duplicates
get_exif_datetime = media_utils.get_exif_datetime
get_video_datetime = media_utils.get_video_datetime
get_media_datetime = media_utils.get_media_datetime
format_shooting_time = media_utils.format_shooting_time

# 支持的图片和视频扩展名
IMAGE_EXTENSIONS = media_utils.IMAGE_EXTENSIONS
VIDEO_EXTENSIONS = media_utils.VIDEO_EXTENSIONS
MEDIA_EXTENSIONS = media_utils.MEDIA_EXTENSIONS

def copy_files_by_types(source_dir: str, dest_dir: str, file_types=None, exclude_dirs=None):
      # 验证路径有效性
    if not os.path.isdir(source_dir):
        logger.error("错误: 源目录不存在或不是目录")
        exit(1)
    
    logger.info(f"开始复制文件: {source_dir} → {dest_dir}")
    report = copy_files_with_conflict_resolution(source_dir, dest_dir, file_types)
    
    # 生成并记录报告
    report_str = generate_conflict_report(report)
    logger.info("操作完成! 文件复制统计:")
    logger.info(report_str)


def move_files_by_types(source_dir: str, dest_dir: str, file_types=None, exclude_dirs=None):
    """
    分类图片和视频：
    - 图片移动到image目录
    - 视频移动到video目录
    """
    
    image_count = 0
    video_count = 0
    # 递归遍历目录
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for filename in files:
          filepath = os.path.join(root, filename)

          # 获取文件扩展名
          _, ext = os.path.splitext(filename)
          ext = ext.lower()
          if not file_types:
            move_file_with_conflict_resolution(filepath, dest_dir)
            image_count += 1
          else:
             if ext in file_types:
              move_file_with_conflict_resolution(filepath, dest_dir)
              image_count += 1
    logger.info(f"分类完成! 图片: {image_count}张, 视频: {video_count}张")

    
def classify_and_rename_media(source_path, file_types):
    """
    步骤1: 分类照片到camera和photo目录
    """
    
    # 执行处理步骤
    camera_dir, no_camera_dir = media_utils.classify_media(source_path, file_types)
    logger.info("==================================\n\n")
    
    # 步骤3
    media_utils.rename_media(camera_dir) 
    logger.info("==================================\n\n")
    
    # 步骤4
    #media_utils.group_by_year(camera_dir)  
    #media_utils.group_by_year_month(camera_dir)
    logger.info("==================================\n\n")
    
    # 步骤: 重命名no_camera目录中的文件
    media_utils.rename_no_camera_files(no_camera_dir)
    logger.info("==================================\n\n")


def main():
    parser = argparse.ArgumentParser(description='整理照片工具')
    parser.add_argument('source_dir', type=str, help='源目录路径')
    parser.add_argument('target_dir', type=str, help='目标目录路径')
    
    # 
    parser.add_argument('--no-copy',  action='store_true', help='不复制文件（默认复制文件）')
    args = parser.parse_args()
    logger.info(f"no_copy value: {args.no_copy}")
    
    source_path = os.path.abspath(args.source_dir)
    if not os.path.isdir(source_path):
        logger.error(f"目录不存在: {source_path}")
        sys.exit(1)
    
    target_path = os.path.abspath(args.target_dir)
    groups = [
       ('image', IMAGE_EXTENSIONS),
       ('video', VIDEO_EXTENSIONS),
    ]
    for group in groups:
       # 创建目标目录
       child_name = group[0]
       file_types = group[1]
       logger.info(f'handle child {child_name} file types {file_types}')
       child_dir = os.path.join(target_path, child_name)
       os.makedirs(child_dir, exist_ok=True)

       # 拷贝文件
       if not args.no_copy:
        copy_files_by_types(source_path, child_dir, file_types=file_types)
        logger.info("==================================\n\n")

       # 删除所有重复文件
       logger.info(f"删除所有重复文件: {target_path}")
       find_and_delete_duplicates(target_path, recursive=True)
       logger.info("==================================\n\n")

       # 分类文件
       logger.info(f"移动文件: {target_path}")
       exclude_dirs = [child_name]
       move_files_by_types(target_path, child_dir, file_types=file_types, exclude_dirs=exclude_dirs)
       logger.info("==================================\n\n")
       
       # 分类和重命名文件
       classify_and_rename_media(child_dir, file_types)
    logger.info("照片整理完成!")


if __name__ == "__main__":
    main()
