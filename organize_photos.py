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
from file_utils import *
from media_utils import *
from duplicate_utils import *
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

def copy_files_by_types(source_dir: str, dest_dir: str, file_types=None, exclude_dirs=None):
      # 验证路径有效性
    if not os.path.isdir(source_dir):
        logger.error("错误: 源目录不存在或不是目录")
        exit(1)
    
    logger.info(f"开始复制文件: {source_dir} → {dest_dir}")
    report = copy_files_with_unique_name(source_dir, dest_dir, file_types)
    
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
            move_file_with_unique_name(filepath, dest_dir)
            image_count += 1
          else:
             if ext in file_types:
              move_file_with_unique_name(filepath, dest_dir)
              image_count += 1
    logger.info(f"分类完成! 图片: {image_count}张, 视频: {video_count}张")

    
def classify_and_rename_media(source_path, file_types, group_type):
    """
    步骤1: 分类照片到camera和photo目录
    """
    
    # 执行处理步骤
    camera_dir, no_camera_dir = classify_media(source_path, file_types)
    logger.info("==================================\n\n")
    
    # 步骤3
    rename_media(camera_dir) 
    logger.info("==================================\n\n")
    
    # # 步骤4
    use_month = True
    if group_type == 'year':
        use_month = False
    group_by_year_and_month(camera_dir, use_month=use_month)  
    logger.info("==================================\n\n")
    
    # # 步骤: 重命名no_camera目录中的文件
    rename_no_camera_files(no_camera_dir)
    logger.info("==================================\n\n")


def process_media_group(group: tuple, 
                        source_path: str, 
                        target_path: str, 
                        no_copy: bool, 
                        group_type: str,
                        duplicate: bool) -> None:
    """
    处理特定媒体类型组（如图片或视频）
    
    Args:
        group: 包含媒体类型名称和扩展名元组的元组
        source_path: 源目录路径
        target_path: 目标目录路径
        no_copy: 是否跳过复制文件
    """
    child_name, file_types = group
    logger.info(f'处理媒体类型: {child_name}, 文件类型: {file_types}')
    
    # 创建目标子目录
    child_dir = os.path.join(target_path, child_name)
    try:
        os.makedirs(child_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"创建目录失败: {child_dir}, 错误: {e}")
        return

    # 复制文件
    if not no_copy:
        try:
            copy_files_by_types(source_path, child_dir, file_types=file_types)
        except Exception as e:
            logger.error(f"复制文件失败: {e}")
        logger.info("==================================\n\n")

    # 删除重复文件
    if duplicate:
      logger.info(f"删除重复文件: {target_path}")
      try:
          find_and_delete_duplicates(target_path, recursive=True)
      except Exception as e:
          logger.error(f"删除重复文件失败: {e}")
      logger.info("==================================\n\n")

    # 移动文件
    logger.info(f"移动文件到分类目录: {child_dir}")
    try:
        exclude_dirs = [child_name]
        move_files_by_types(target_path, child_dir, file_types=file_types, exclude_dirs=exclude_dirs)
    except Exception as e:
        logger.error(f"移动文件失败: {e}")
    logger.info("==================================\n\n")
    
    # 分类和重命名文件
    try:
        classify_and_rename_media(child_dir, file_types, group_type)
    except Exception as e:
        logger.error(f"分类和重命名失败: {e}")


def main():
    parser = argparse.ArgumentParser(description='整理照片工具')
    parser.add_argument('source_dir', type=str, help='源目录路径')
    parser.add_argument('target_dir', type=str, help='目标目录路径')
    parser.add_argument('--no-copy', action='store_true', help='不复制文件（默认复制文件）')
    parser.add_argument('--group', type=str, help='分组类型（year/month/day）', default='year')
    parser.add_argument('--duplicate', action='store_true', help='删除重复文件')
    
    args = parser.parse_args()
    logger.info(f"参数设置: no_copy={args.no_copy} group={args.group} duplicate={args.duplicate}")
    
    source_path = os.path.abspath(args.source_dir)
    if not os.path.isdir(source_path):
        logger.error(f"目录不存在: {source_path}")
        sys.exit(1)
    
    target_path = os.path.abspath(args.target_dir)
    os.makedirs(target_path, exist_ok=True)
    
    # 检查目标目录是否可写
    if not os.access(target_path, os.W_OK):
        logger.error(f"目标目录不可写: {target_path}")
        sys.exit(1)
    
    media_groups = [
        ('image', IMAGE_EXTENSIONS),
        ('video', VIDEO_EXTENSIONS),
    ]
    
    for group in media_groups:
        process_media_group(group, source_path, target_path, args.no_copy, args.group, args.duplicate)
    
    logger.info("照片整理完成!")


if __name__ == "__main__":
    main()
