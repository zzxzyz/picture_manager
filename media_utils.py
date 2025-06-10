"""
媒体处理工具模块
包含EXIF信息提取、拍摄时间处理等功能
"""

import os
import subprocess
import logging
from PIL import Image, ExifTags
from datetime import datetime

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


def classify_media(source_path, camera_dir, photo_dir):
    """分类媒体文件到camera和photo目录"""
    logger.info(f"开始分类媒体文件: {source_path}")
    
    for filename in os.listdir(source_path):
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
    logger.info(f"媒体分类完成! camera: {camera_count}个, photo: {photo_count}个")


def rename_media(camera_dir):
    """重命名媒体文件"""
    logger.info(f"开始重命名媒体文件: {camera_dir}")
    
    renamed_count = 0
    skipped_count = 0
    
    for filename in os.listdir(camera_dir):
        file_path = os.path.join(camera_dir, filename)
        if not os.path.isfile(file_path) or filename == '.DS_Store':
            continue
            
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
            
        dt_obj = format_shooting_time(dt_str=dt_str)
        if not dt_obj:
            continue
            
        expeted_name = f"{prefix}_{dt_obj}"
        if expeted_name in filename:
            logger.info(f"跳过重命名: {filename} 已符合命名规则")
            skipped_count += 1
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
            skipped_count += 1
    
    logger.info(f"重命名完成! 已重命名: {renamed_count}个, 跳过: {skipped_count}个")


def group_by_year(camera_dir):
    """按年份分组媒体文件"""
    logger.info(f"开始按年份分组媒体文件: {camera_dir}")
    
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
                if move_file_with_conflict_resolution(file_path, year_dir):
                    moved_count += 1
    
    logger.info(f"年份分组完成! 已移动: {moved_count}个文件")


def set_file_creation_date(filepath, dt_str):
    """设置文件的创建时间为拍摄时间"""
    try:
        dt_obj = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        timestamp = dt_obj.timestamp()
        os.utime(filepath, (timestamp, timestamp))
        logger.info(f"设置创建时间成功: {filepath} -> {dt_str}")
        return True
    except Exception as e:
        logger.error(f"设置创建时间失败: {filepath} - {str(e)}")
        return False


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
                set_file_creation_date(filepath, dt_str)
