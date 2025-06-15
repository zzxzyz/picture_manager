"""
时间处理工具模块
"""
import os
import logging
from datetime import datetime
import exifread
import subprocess
import json

logger = logging.getLogger(__name__)

def get_capture_time(file_path, media_type):
    """
    获取媒体文件的拍摄时间
    
    :param file_path: 文件路径
    :param media_type: 媒体类型（'images'或'videos'）
    :return: datetime对象或None
    """
    try:
        if media_type == 'images':
            return get_image_capture_time(file_path)
        elif media_type == 'videos':
            return get_video_capture_time(file_path)
    except Exception as e:
        logger.error(f"获取 {file_path} 拍摄时间失败: {str(e)}")
    return None

def get_image_capture_time(file_path):
    """获取图片拍摄时间"""
    # 使用exifread读取EXIF信息
    with open(file_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
        
        # 尝试不同的EXIF标签
        for tag in ['EXIF DateTimeOriginal', 'Image DateTime']:
            if tag in tags:
                time_str = str(tags[tag])
                return parse_time_string(time_str)
    
    return None

def get_video_capture_time(file_path):
    """获取视频拍摄时间"""
    # 使用ffprobe获取视频元数据
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format_tags=creation_time',
        '-of', 'json',
        file_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        metadata = json.loads(result.stdout)
        creation_time = metadata.get('format', {}).get('tags', {}).get('creation_time')
        if creation_time:
            return parse_time_string(creation_time)
    
    return None

def parse_time_string(time_str):
    """
    解析各种格式的时间字符串
    
    支持的格式:
    - YYYY:MM:DD HH:MM:SS
    - YYYY-MM-DD HH:MM:SS
    - YYYYMMDD_HHMMSS
    - ISO 8601格式
    """
    # 尝试常见格式
    formats = [
        '%Y:%m:%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y%m%d_%H%M%S',
        '%Y-%m-%dT%H:%M:%S.%fZ'  # ISO 8601
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    # 如果都不匹配，尝试更宽松的解析
    try:
        # 移除时区信息
        if '+' in time_str:
            time_str = time_str.split('+')[0]
        
        # 尝试解析为ISO格式
        return datetime.fromisoformat(time_str)
    except (ValueError, TypeError):
        logger.warning(f"无法解析时间字符串: {time_str}")
        return None
