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
create_target_filename = file_utils.create_target_filename

# 支持的图片和视频扩展名
IMAGE_EXTENSIONS = media_utils.IMAGE_EXTENSIONS
VIDEO_EXTENSIONS = media_utils.VIDEO_EXTENSIONS
MEDIA_EXTENSIONS = media_utils.MEDIA_EXTENSIONS

def mere_all_files(source_dir: str, dest_dir: str):
      # 验证路径有效性
    if not os.path.isdir(source_dir):
        logger.error("错误: 源目录不存在或不是目录")
        exit(1)
    
    logger.info(f"开始复制文件: {source_dir} → {dest_dir}")
    report = copy_files_with_conflict_resolution(source_dir, dest_dir)
    
    # 生成并记录报告
    report_str = generate_conflict_report(report)
    logger.info("操作完成! 文件复制统计:")
    logger.info(report_str)


def classify_files(directory):
    """
    分类目录中的文件：
    - 图片移动到image目录
    - 视频移动到video目录
    - 其他文件保留在根目录
    """
    # 创建目标目录
    image_dir = os.path.join(directory, 'image')
    video_dir = os.path.join(directory, 'video')
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)
    
    # 遍历目录中的文件
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # 跳过目录
        if os.path.isdir(filepath):
            continue
            
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # 分类文件
        if ext in IMAGE_EXTENSIONS:
            move_file_with_conflict_resolution(filepath, image_dir)
            
        elif ext in VIDEO_EXTENSIONS:
            move_file_with_conflict_resolution(filepath, video_dir)
        else:
            logger.info(f"保留文件: {filename}")

def classify_media(source_path, camera_dir, photo_dir):
    """
    步骤1: 分类照片到camera和photo目录
    """
    logger.info(f"开始分类照片: {source_path}")
    
    # 获取所有文件
    all_files = os.listdir(source_path)
    for filename in all_files:
        file_path = os.path.join(source_path, filename)
        if not os.path.isfile(file_path):
            continue
            
        _, ext = os.path.splitext(filename)
        if ext.lower() in MEDIA_EXTENSIONS:
            dt_str = get_media_datetime(file_path)
            dt_obj = format_shooting_time(dt_str=dt_str)
            if dt_obj:
                logger.info(f"{filename} [拍摄时间: {dt_str}] -> {camera_dir}")
                move_file_with_conflict_resolution(file_path, camera_dir)
            else:
                logger.info(f"{filename} [拍摄时间:无] -> {photo_dir}")
                move_file_with_conflict_resolution(file_path, photo_dir)
    
    camera_count = len(os.listdir(camera_dir))
    photo_count = len(os.listdir(photo_dir))
    logger.info(f"照片分类完成! camera: {camera_count}张, photo: {photo_count}张")


def rename_media(camera_dir):
    """
    步骤3: 重命名照片文件
    """
    logger.info(f"开始重命名照片: {camera_dir}")
    
    # 第一步：收集所有需要处理的文件
    file_list = []
    ignore_list = ['.DS_Store']
    for filename in os.listdir(camera_dir):
        file_path = os.path.join(camera_dir, filename)
        if not os.path.isfile(file_path) or filename in ignore_list:
            continue
        file_list.append(file_path)
    
    # 第二步：处理所有收集到的文件
    renamed_count = 0
    skipped_count = 0
    
    for file_path in file_list:
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)
        if ext in IMAGE_EXTENSIONS:
            prefix = "IMG"
        elif ext in VIDEO_EXTENSIONS:
            prefix = "VID"
        else:
            continue
        dt_str = get_media_datetime(file_path)
        if not dt_str:
            continue
        # 如果filename 已经包括dst_str，则跳过
        dt_obj = format_shooting_time(dt_str=dt_str)
        if dt_obj is None:
          continue
        expeted_name = f"{prefix}_{dt_obj}"
        if expeted_name in filename:
            logger.info(f"跳过重命名: {filename} 已符合命名规则, 拍摄时间: {dt_obj}")
            continue
        new_name = create_target_filename(prefix, dt_obj, ext, os.listdir(camera_dir))
        
        if not new_name:
            skipped_count += 1
            continue
            
        if filename != new_name:
            new_path = os.path.join(camera_dir, new_name)
            os.rename(file_path, new_path)
            logger.info(f"重命名: {filename} -> {new_name}")
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
            
        if (filename.startswith("IMG_") or filename.startswith("VID_")) and len(filename) >= 12:
            year = filename[4:8]  # 从 IMG_YYYYMMDD... 提取年份
            if year.isdigit():
                year_dir = os.path.join(camera_dir, year)
                if not os.path.exists(year_dir):
                    os.makedirs(year_dir)
                is_moved = move_file_with_conflict_resolution(file_path, year_dir)
                if is_moved:
                  moved_count += 1
    
    logger.info(f"年份分组完成! 已移动: {moved_count}张照片")
    
    
def classify_and_rename_media(source_path):
    """
    步骤1: 分类照片到camera和photo目录
    """
    # 创建分类目录
    camera_dir = os.path.join(source_path, "camera")
    no_camera_dir = os.path.join(source_path, "no_camera")
    
    if not os.path.exists(camera_dir):
        os.makedirs(camera_dir)
    if not os.path.exists(no_camera_dir):
        os.makedirs(no_camera_dir)
    
    # 执行处理步骤
    classify_media(source_path, camera_dir, no_camera_dir)
    logger.info("==================================\n\n")
    
    # 步骤3
    rename_media(camera_dir) 
    logger.info("==================================\n\n")
    
    # 新增步骤：设置照片创建时间为拍摄时间
    # logger.info(f"设置照片创建时间为拍摄时间: {camera_dir}")
    # set_creation_time_for_photos(camera_dir)
    # logger.info("==================================\n\n")
    
    # 步骤4
    # group_by_year(camera_dir)  
    # logger.info("==================================\n\n")
    
    # 步骤: 重命名no_camera目录中的文件
    logger.info(f"开始处理no_camera目录: {no_camera_dir}")
    rename_no_camera_files(no_camera_dir)
    logger.info("==================================\n\n")


def main():
    parser = argparse.ArgumentParser(description='整理照片工具')
    parser.add_argument('source_dir', type=str, help='源目录路径')
    parser.add_argument('target_dir', type=str, help='目标目录路径')
    args = parser.parse_args()
    
    source_path = os.path.abspath(args.source_dir)
    if not os.path.isdir(source_path):
        logger.error(f"目录不存在: {source_path}")
        sys.exit(1)
    
    # 合并所有文件
    target_path = os.path.abspath(args.target_dir)
    logger.info(f"开始合并所有文件: {source_path} → {target_path}")
    mere_all_files(source_path, target_path)
    logger.info("==================================\n\n")
    
    # 删除所有重复文件
    logger.info(f"删除所有重复文件: {target_path}")
    find_and_delete_duplicates(target_path)
    logger.info("==================================\n\n")
    
    # 分类文件
    logger.info(f"分类文件: {target_path}")
    classify_files(target_path)
    logger.info("==================================\n\n")
    
    # 分类和重命名文件
    image_path = os.path.join(target_path, "image")
    classify_and_rename_media(image_path)
    
    video_path = os.path.join(target_path, "video")
    classify_and_rename_media(video_path)
    
    # 遍历target_path目录下的所有子目录
    for root, dirs, files in os.walk(target_path):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if os.path.isdir(dir_path):
                logger.info(f"处理子目录: {dir_path}")
                find_and_delete_duplicates(dir_path)
                logger.info("==================================\n\n")
  
    logger.info("==================================\n\n")
    logger.info("照片整理完成!")


def remane_file_with_confict_resolution(file_path, new_base_name, ext, target_dir):
    """
    解决文件名冲突并重命名文件
    """
    
    new_name = f"{new_base_name}{ext}"
    
    # 解决文件名冲突
    counter = 1
    while os.path.exists(os.path.join(target_dir, new_name)):
        new_name = f"{new_base_name}_{counter}{ext}"
        counter += 1
    
    # 重命名文件
    new_path = os.path.join(target_dir, new_name)
    os.rename(file_path, new_path)
    logger.info(f"重命名: {file_path} -> {new_name}")
    

def rename_no_camera_files(no_camera_dir):
    """
    重命名no_camera目录中的照片文件
    规则1: 跳过符合IMG_YYYYMMDD_HHMMSS格式的文件
    规则2: 处理YYYYMMDD_IMG_HHMM格式的文件（支持带括号）
    规则3: 处理MTXX_YYYYMMDDHHMMSS格式的文件
    规则4: 处理beauty_YYYYMMDDHHMMSS格式的文件
    规则5: 处理pt_YYYY_MM_DD_HH_MM_SS格式的文件
    """
    logger.info(f"开始重命名no_camera目录中的照片: {no_camera_dir}")
    
    # 获取所有文件
    file_list = []
    ignore_list = ['.DS_Store']
    for filename in os.listdir(no_camera_dir):
        file_path = os.path.join(no_camera_dir, filename)
        if not os.path.isfile(file_path) or filename in ignore_list:
            continue
        file_list.append(file_path)
    
    renamed_count = 0
    skipped_count = 0
    
    for file_path in file_list:
        filename = os.path.basename(file_path)
        base_name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # 只处理图片文件
        if ext not in IMAGE_EXTENSIONS:
            continue
        
        # 规则1: 跳过符合IMG_YYYYMMDD_HHMMSS格式的文件
        if re.match(r'^IMG_\d{8}_\d{6}$', base_name):
            logger.info(f"跳过重命名(规则1): {filename} 已符合命名规则")
            skipped_count += 1
            continue
        
        # 规则2: 处理YYYYMMDD_IMG_HHMM格式的文件（支持带括号）
        match = re.match(r'^(\d{8})_IMG_(\d{4}).*$', base_name)
        if match:
            date_part = match.group(1)
            time_part = match.group(2)
            new_base_name = f"IMG_{date_part}_{time_part}00"
            remane_file_with_confict_resolution(file_path, new_base_name, ext, no_camera_dir)
            renamed_count += 1
            continue
        
        # 规则3: 处理MTXX_YYYYMMDDHHMMSS格式的文件
        match = re.match(r'^MTXX_(\d{8})(\d{6})$', base_name)
        if match:
            date_part = match.group(1)
            time_part = match.group(2)
            new_base_name = f"IMG_{date_part}_{time_part}"
            remane_file_with_confict_resolution(file_path, new_base_name, ext, no_camera_dir)
            renamed_count += 1
            continue
        
        # 规则4: 处理beauty_YYYYMMDDHHMMSS格式的文件
        match = re.match(r'^beauty_(\d{8})(\d{6}).*$', base_name)
        if match:
            date_part = match.group(1)
            time_part = match.group(2)
            new_base_name = f"IMG_{date_part}_{time_part}"
            remane_file_with_confict_resolution(file_path, new_base_name, ext, no_camera_dir)
            renamed_count += 1
            continue
        
        # 规则5: 处理pt_YYYY_MM_DD_HH_MM_SS格式的文件
        match = re.match(r'^pt(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})$', base_name)
        if match:
            year = match.group(1)
            month = match.group(2)
            day = match.group(3)
            hour = match.group(4)
            minute = match.group(5)
            second = match.group(6)
            
            date_part = f"{year}{month}{day}"
            time_part = f"{hour}{minute}{second}"
            new_base_name = f"IMG_{date_part}_{time_part}"
            remane_file_with_confict_resolution(file_path, new_base_name, ext, no_camera_dir)
            renamed_count += 1
            continue
        
        #规则6: 其它照片，统一重命名为文件的修改时间
        try:
            mod_time = os.path.getmtime(file_path)
            dt_obj = datetime.fromtimestamp(mod_time)
            
            # 格式化时间并处理异常
            try:
                formatted_time = dt_obj.strftime('%Y:%m:%d %H:%M:%S')
                logger.info(f"{filename} [修改时间: {formatted_time}]")
                
                # 创建新文件名
                date_str = dt_obj.strftime('%Y%m%d')
                time_str = dt_obj.strftime('%H%M%S')
                new_base_name = f"IMG_{date_str}_{time_str}"
                remane_file_with_confict_resolution(file_path, new_base_name, ext, no_camera_dir)
                renamed_count += 1
            except Exception as e:
                logger.error(f"格式化时间失败: {filename} - {str(e)}")
                skipped_count += 1
        except Exception as e:
            logger.error(f"获取修改时间失败: {filename} - {str(e)}")
            skipped_count += 1
        
        # 其他文件跳过
        # logger.info(f"跳过重命名: {filename} 不符合任何规则")
        # skipped_count += 1
    
    logger.info(f"no_camera目录重命名完成! 已重命名: {renamed_count}张, 跳过: {skipped_count}张")

if __name__ == "__main__":
    main()
