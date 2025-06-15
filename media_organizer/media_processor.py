"""
媒体处理核心模块
"""
import os
import re
import shutil
import logging
from datetime import datetime
from . import time_utils

logger = logging.getLogger(__name__)

# 支持的图片和视频格式
IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
VIDEO_EXTS = ['.mp4', '.mov', '.avi', '.mkv', '.flv']

# 文件命名正则规则
NAME_PATTERNS = [
    r'(\d{8})_IMG_(\d{4})',  # YYYYMMDD_IMG_HHMM
    r'MTXX_(\d{8})_(\d{6})',  # MTXX_YYYYMMDD_HHMMSS
    r'pt(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})',  # ptYYYY_MM_DD_HH_MM_SS
    r'beauty_(\d{12})'  # beauty_YYYMMDDHHMMSS
]

def process_images(target_dir):
    """处理图片文件"""
    logger.info("开始处理图片文件")
    
    # 4.1 收集目标目录中散落的图片
    image_dir = os.path.join(target_dir, 'images')
    other_images = []
    for root, _, files in os.walk(target_dir):
        # 跳过images目录本身
        if root.startswith(image_dir):
            continue
            
        for file in files:
            if os.path.splitext(file)[1].lower() in IMAGE_EXTS:
                other_images.append(os.path.join(root, file))
    
    # 复制到images目录
    for src_path in other_images:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(image_dir, filename)
        
        # 处理文件名冲突
        counter = 1
        while os.path.exists(dest_path):
            name, ext = os.path.splitext(filename)
            dest_path = os.path.join(image_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        shutil.move(src_path, dest_path)
        logger.info(f"移动图片: {src_path} -> {dest_path}")
    
    # 4.2 分类图片
    classify_media(image_dir, 'images')
    
    # 4.3 处理camera目录
    process_camera_dir(os.path.join(image_dir, 'camera'))
    
    # 4.4 处理no_camera目录
    process_no_camera_dir(os.path.join(image_dir, 'no_camera'))
    
    logger.info("图片处理完成")

def process_videos(target_dir):
    """处理视频文件"""
    logger.info("开始处理视频文件")
    
    # 5.1 收集目标目录中散落的视频
    video_dir = os.path.join(target_dir, 'videos')
    other_videos = []
    for root, _, files in os.walk(target_dir):
        # 跳过videos目录本身
        if root.startswith(video_dir):
            continue
            
        for file in files:
            if os.path.splitext(file)[1].lower() in VIDEO_EXTS:
                other_videos.append(os.path.join(root, file))
    
    # 复制到videos目录
    for src_path in other_videos:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(video_dir, filename)
        
        # 处理文件名冲突
        counter = 1
        while os.path.exists(dest_path):
            name, ext = os.path.splitext(file)
            dest_path = os.path.join(video_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        shutil.move(src_path, dest_path)
        logger.info(f"移动视频: {src_path} -> {dest_path}")
    
    # 5.2 分类视频
    classify_media(video_dir, 'videos')
    
    # 5.3 处理camera目录
    process_camera_dir(os.path.join(video_dir, 'camera'))
    
    # 5.4 处理no_camera目录
    process_no_camera_dir(os.path.join(video_dir, 'no_camera'))
    
    logger.info("视频处理完成")

def classify_media(media_dir, media_type):
    """
    将媒体文件分类到camera和no_camera目录
    
    :param media_dir: 媒体目录（images或videos）
    :param media_type: 媒体类型（'images'或'videos'）
    """
    camera_dir = os.path.join(media_dir, 'camera')
    no_camera_dir = os.path.join(media_dir, 'no_camera')
    os.makedirs(camera_dir, exist_ok=True)
    os.makedirs(no_camera_dir, exist_ok=True)
    
    for root, _, files in os.walk(media_dir):
        # 跳过已经分类的目录
        if root == camera_dir or root == no_camera_dir:
            continue
            
        for file in files:
            src_path = os.path.join(root, file)
            
            # 获取拍摄时间
            capture_time = time_utils.get_capture_time(src_path, media_type)
            
            if capture_time:
                # 有拍摄时间 -> camera目录
                dest_dir = camera_dir
                # 打印两种格式的时间
                formatted_time = capture_time.strftime('%Y:%m:%d %H:%M:%S')
                compact_time = capture_time.strftime('%Y%m%d_%H%M%S')
                logger.info(f"{file} 拍摄时间: {formatted_time} / {compact_time}")
            else:
                # 无拍摄时间 -> no_camera目录
                dest_dir = no_camera_dir
                logger.info(f"{file} 无拍摄时间信息")
            
            # 移动文件
            dest_path = os.path.join(dest_dir, file)
            
            # 处理文件名冲突
            counter = 1
            while os.path.exists(dest_path):
                name, ext = os.path.splitext(file)
                dest_path = os.path.join(dest_dir, f"{name}_{counter}{ext}")
                counter += 1
            
            shutil.move(src_path, dest_path)
            logger.info(f"分类: {file} -> {os.path.basename(dest_dir)}")

def process_camera_dir(camera_dir):
    """处理camera目录：重命名和分组"""
    if not os.path.exists(camera_dir):
        return
        
    for root, _, files in os.walk(camera_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            # 4.3.1/5.3.1 检查文件名是否符合规范
            if not is_valid_filename(file):
                # 不符合规范，使用拍摄时间重命名
                media_type = 'images' if 'images' in camera_dir else 'videos'
                capture_time = time_utils.get_capture_time(file_path, media_type)
                
                if capture_time:
                    new_name = f"IMG_{capture_time.strftime('%Y%m%d_%H%M%S')}{os.path.splitext(file)[1]}"
                    new_path = os.path.join(root, new_name)
                    
                    # 处理文件名冲突
                    counter = 1
                    while os.path.exists(new_path):
                        name, ext = os.path.splitext(new_name)
                        new_path = os.path.join(root, f"{name}_{counter}{ext}")
                        counter += 1
                    
                    os.rename(file_path, new_path)
                    logger.info(f"重命名: {file} -> {new_name}")
                    file_path = new_path
                
            # 4.3.2/5.3.2 分组
            group_by_date(file_path, camera_dir)

def process_no_camera_dir(no_camera_dir):
    """处理no_camera目录：重命名和分组"""
    if not os.path.exists(no_camera_dir):
        return
        
    for root, _, files in os.walk(no_camera_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            # 4.4.1 尝试从文件名提取时间信息
            capture_time = extract_time_from_filename(file)
            
            if capture_time:
                # 重命名文件
                new_name = f"IMG_{capture_time.strftime('%Y%m%d_%H%M%S')}{os.path.splitext(file)[1]}"
                new_path = os.path.join(root, new_name)
                
                # 处理文件名冲突
                counter = 1
                while os.path.exists(new_path):
                    name, ext = os.path.splitext(new_name)
                    new_path = os.path.join(root, f"{name}_{counter}{ext}")
                    counter += 1
                
                os.rename(file_path, new_path)
                logger.info(f"重命名(从文件名): {file} -> {new_name}")
                file_path = new_path
            
            # 4.4.2/5.4.1 分组
            group_by_date(file_path, no_camera_dir)

def is_valid_filename(filename):
    """检查文件名是否符合IMG_YYYYMMDD_HHMMSS格式"""
    pattern = r'^IMG_\d{8}_\d{6}\..+$'
    return re.match(pattern, filename) is not None

def extract_time_from_filename(filename):
    """从文件名中提取时间信息"""
    for pattern in NAME_PATTERNS:
        match = re.search(pattern, filename)
        if match:
            try:
                if pattern == NAME_PATTERNS[0]:  # YYYYMMDD_IMG_HHMM
                    date_str = match.group(1)
                    time_str = match.group(2) + '00'  # 添加秒
                    return datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                
                elif pattern == NAME_PATTERNS[1]:  # MTXX_YYYYMMDD_HHMMSS
                    date_str = match.group(1)
                    time_str = match.group(2)
                    return datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                
                elif pattern == NAME_PATTERNS[2]:  # ptYYYY_MM_DD_HH_MM_SS
                    year = match.group(1)
                    month = match.group(2)
                    day = match.group(3)
                    hour = match.group(4)
                    minute = match.group(5)
                    second = match.group(6)
                    return datetime.strptime(
                        f"{year}{month}{day}{hour}{minute}{second}", 
                        "%Y%m%d%H%M%S"
                    )
                
                elif pattern == NAME_PATTERNS[3]:  # beauty_YYYMMDDHHMMSS
                    time_str = match.group(1)
                    # 处理可能的3位数年份
                    if len(time_str) == 12:
                        return datetime.strptime(time_str, "%Y%m%d%H%M%S")
                    elif len(time_str) == 11:
                        return datetime.strptime(time_str, "%y%m%d%H%M%S")
            except ValueError:
                continue
    return None

def group_by_date(file_path, base_dir):
    """
    根据文件时间信息分组
    
    :param file_path: 文件路径
    :param base_dir: 基础目录（camera或no_camera）
    """
    filename = os.path.basename(file_path)
    
    # 尝试从文件名解析日期
    try:
        # 格式: IMG_YYYYMMDD_HHMMSS.ext
        date_str = filename.split('_')[1]
        file_date = datetime.strptime(date_str, "%Y%m%d")
    except (IndexError, ValueError):
        logger.info(f"无法从文件名解析日期: {filename}")
        return
    
    # 创建分组目录（按年月）
    group_dir = os.path.join(base_dir, file_date.strftime('%Y-%m'))
    os.makedirs(group_dir, exist_ok=True)
    
    # 移动文件到分组目录
    dest_path = os.path.join(group_dir, filename)
    
    # 处理文件名冲突
    counter = 1
    while os.path.exists(dest_path):
        name, ext = os.path.splitext(filename)
        dest_path = os.path.join(group_dir, f"{name}_{counter}{ext}")
        counter += 1
    
    shutil.move(file_path, dest_path)
    logger.info(f"分组: {filename} -> {os.path.basename(group_dir)}")
