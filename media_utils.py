"""
媒体处理工具模块
包含EXIF信息提取、拍摄时间处理等功能
"""

import os
import re
import subprocess
import logging
from PIL import Image, ExifTags
from datetime import datetime
import file_utils

#from file_utils import create_target_filename, move_file_with_conflict_resolution

logger = logging.getLogger(__name__)

# 支持的图片和视频扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg', '.3gp', '.m4v'}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

def get_exif_datetime(image_path):
    """
    获取照片的拍摄时间
    """
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()
            if exif:
                for tag, value in exif.items():
                    if ExifTags.TAGS.get(tag) == 'DateTimeOriginal':
                        clean_value = value.split('.')[0][:19]
                        return clean_value
    except Exception as e:
        logger.error(f"读取 {image_path} EXIF 失败: {str(e)}")
    return None


def get_video_datetime(filepath):
    """
    获取视频的拍摄时间
    """
    try:
        result = subprocess.run(
            ['exiftool', '-CreateDate', '-d', '%Y:%m:%d %H:%M:%S', '-T', filepath],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        if output and output != '-':
            clean_value = output.split('.')[0][:19]
            return clean_value
    except subprocess.CalledProcessError as e:
        logger.error(f"读取 {filepath} 拍摄时间失败: {str(e)}")
    except Exception as e:
        logger.error(f"处理 {filepath} 拍摄时间失败: {str(e)}")
    return None


def get_media_datetime(filepath):
    """
    获取媒体文件（图片或视频）的拍摄时间
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    if ext in IMAGE_EXTENSIONS:
        return get_exif_datetime(filepath)
    elif ext in VIDEO_EXTENSIONS:
        return get_video_datetime(filepath)
    return None


def format_shooting_time(dt_str):
    """
    格式化拍摄时间
    """
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S").strftime('%Y%m%d_%H%M%S')
    except ValueError:
        logger.error(f"无效的日期时间格式: {dt_str}")
        return None


def classify_media(source_path, file_types):
    """
    分类媒体文件到camera和no_camera目录
    -有拍摄时间的文件放到camera目录
    -没有拍摄时间的文件放到no_camera目录
    """
    logger.info(f"开始分类照片: {source_path}")
    
        # 创建分类目录
    camera_dir = os.path.join(source_path, "camera")
    no_camera_dir = os.path.join(source_path, "no_camera")
    
    if not os.path.exists(camera_dir):
        os.makedirs(camera_dir)
    if not os.path.exists(no_camera_dir):
        os.makedirs(no_camera_dir)
    
    # 获取所有文件
    camera_count = 0
    no_camera_count = 0
    exclude_dirs = ['camera', 'no_camera']
    # 递归遍历目录
    for root, dirs, files in os.walk(source_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for filename in files:
          file_path = os.path.join(root, filename)
          _, ext = os.path.splitext(filename)
          if ext.lower() in file_types:
              dt_str = get_media_datetime(file_path)
              dt_obj = format_shooting_time(dt_str=dt_str)
              if dt_obj:
                  logger.info(f"{filename} [拍摄时间: {dt_str}] -> {camera_dir}")
                  file_utils.move_file_with_conflict_resolution(file_path, camera_dir)
                  camera_count += 1
              else:
                  logger.info(f"{filename} [拍摄时间:无] -> {no_camera_dir}")
                  file_utils.move_file_with_conflict_resolution(file_path, no_camera_dir)
                  no_camera_count += 1
    
    logger.info(f"照片分类完成! camera: {camera_count}张, no_camera: {no_camera_count}张")
    return camera_dir, no_camera_dir
    
    
def rename_media(camera_dir):
    """
    重命名照片文件
    """
    logger.info(f"开始重命名目录: {camera_dir}")
    
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
            file_pattern = r'^IMG_\d{8}_\d{6}'
        elif ext in VIDEO_EXTENSIONS:
            prefix = "VID"
            file_pattern = r'^VID_\d{8}_\d{6}'
        else:
            continue
        # 规则1: 跳过符合IMG_YYYYMMDD_HHMMSS格式的文件
        if re.match(file_pattern, filename):
            logger.info(f"跳过重命名: {filename} 已符合命名规则")
            skipped_count += 1
            continue
        dt_str = get_media_datetime(file_path)
        if not dt_str:
            continue
        # 如果filename 已经包括dst_str，则跳过
        dt_obj = format_shooting_time(dt_str=dt_str)
        if dt_obj is None:
          continue
        new_name = file_utils.create_target_filename(prefix, dt_obj, ext, os.listdir(camera_dir))
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
    """按年份分组媒体文件"""
    logger.info(f"开始分组目录: {camera_dir}")
    
    moved_count = 0
    for filename in os.listdir(camera_dir):
        file_path = os.path.join(camera_dir, filename)
        if not os.path.isfile(file_path):
            continue
            
        if (filename.startswith("IMG_") or filename.startswith("VID_")) and len(filename) >= 12:
            year = filename[4:8]
            if year.isdigit():
                year_dir = os.path.join(camera_dir, year)
                if not os.path.exists(year_dir):
                    os.makedirs(year_dir)
                if file_utils.move_file_with_conflict_resolution(file_path, year_dir):
                    moved_count += 1
    
    logger.info(f"年份分组完成! 已移动: {moved_count}个文件")



# 按年月分组，并创建对应的目录，目录格式为YYYY-MM
def group_by_year_month(camera_dir):
    """
    步骤4: 按年月分组照片
    """
    logger.info(f"开始按年月分组照片: {camera_dir}")
    
    moved_count = 0
    for filename in os.listdir(camera_dir):
        file_path = os.path.join(camera_dir, filename)
        if not os.path.isfile(file_path):
            continue
            
        if (filename.startswith("IMG_") or filename.startswith("VID_")) and len(filename) >= 12:
            year = filename[4:8]  # 从 IMG_YYYYMMDD... 提取年份
            month = filename[8:10]
            if year.isdigit() and month.isdigit():
                year_month_dir = os.path.join(camera_dir, f"{year}-{month}")
                if not os.path.exists(year_month_dir):
                    os.makedirs(year_month_dir)
                is_moved = file_utils.move_file_with_conflict_resolution(file_path, year_month_dir)
                if is_moved:
                  moved_count += 1
    
    logger.info(f"年月分组完成! 已移动: {moved_count}张照片")


def set_creation_time_for_photos(directory):
    """递归设置照片创建时间为拍摄时间"""
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            _, ext = os.path.splitext(filename)
            if ext.lower() not in IMAGE_EXTENSIONS:
                continue
            dt_str = get_exif_datetime(filepath)
            if dt_str:
                file_utils.set_file_creation_date(filepath, dt_str)


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
    logger.info(f"开始重命名目录: {no_camera_dir}")
    
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
        if re.match(r'^IMG_\d{8}_\d{6}', base_name):
            logger.info(f"跳过重命名: {filename} 已符合命名规则")
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
                new_base_name = f"IMG_{date_str}_{time_str}_NO"
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
