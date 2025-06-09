#!/usr/bin/env python3
"""
照片整理工具
功能：
1. 把源目录的所有文件拷贝到目标目录，并解决文件命名冲突
2. 把目标目录中的文件按md5去重
3. 把目标目录中的图片移动到image, 视频移动到video, 其它文件位置保持不变
4. 把image目录下的照片分类到camera/photo目录，有拍摄时间的分类到camera, 没有拍摄时间的分类到photo
5. 把image/camera目录下的照片用拍摄时间重命名， 照片名称格式为IMG_日期_时间格式.ext
6. 把image/camera目录下的照片按年份分组照片, 比如把image/camera/2013, 把image/camera/2014
7. 删除目录目录下所有子目录的重复文件
"""

import argparse
from collections import defaultdict
import hashlib
import logging
import shutil
import subprocess
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

def copy_files_with_conflict_resolution(src_dir, dest_dir):
    """
    递归复制所有文件到目标目录，解决文件名冲突
    参数:
        src_dir (str): 源目录路径
        dest_dir (str): 目标目录路径
    返回:
        dict: 文件名冲突解决报告
    """
    # 创建目标目录（如果不存在）
    os.makedirs(dest_dir, exist_ok=True)
    
    # 存储文件名计数和冲突解决报告
    name_counter = defaultdict(int)
    conflict_report = {}

    ignore_list = ['.DS_Store']

    # 递归遍历源目录
    for root, _, files in os.walk(src_dir):
        for filename in files:
            if filename in ignore_list:
                continue
            src_path = os.path.join(root, filename)
            
            # 生成基本目标路径
            base_name, ext = os.path.splitext(filename)
            ext = ext.lower()
            dest_name = f"{base_name}{ext}"
            conflict_level = 0
            
            # 处理文件名冲突
            while os.path.exists(os.path.join(dest_dir, dest_name)):
                conflict_level += 1
                dest_name = f"{base_name}_{conflict_level}{ext}"
            
            # 更新文件名计数器
            name_counter[filename] += 1
            
            # 复制文件
            dest_path = os.path.join(dest_dir, dest_name)
            shutil.copy2(src_path, dest_path)
            
            # 记录冲突解决情况
            if conflict_level > 0:
                conflict_report[src_path] = {
                    "original_name": filename,
                    "new_name": dest_name,
                    "conflict_level": conflict_level
                }
            
            logger.info(f"复制: {src_path} -> {dest_path}")
    
    return conflict_report


def generate_conflict_report(report):
    """
    生成文件名冲突解决报告
    
    参数:
        report (dict): 冲突解决报告字典，包含以下结构:
            {
                "源文件路径1": {
                    "original_name": "原文件名",
                    "new_name": "新文件名",
                    "conflict_level": "冲突级别"
                },
                "源文件路径2": { ... }
            }
            
    返回值:
        str: 格式化的冲突解决报告字符串
        
    报告格式说明:
        - 如果report为空，返回未发生冲突的消息
        - 否则返回包含以下内容的表格化报告:
            1. 表头: 源文件路径、原文件名、新文件名、冲突级别
            2. 每行一个冲突解决记录
            3. 底部显示冲突解决总数
    """
    if not report:
        return "✅ 未发生文件名冲突\n"
    
    report_str = "\n📊 文件名冲突解决报告:\n"
    report_str += "-" * 60 + "\n"
    report_str += f"{'源文件路径':<40} {'原文件名':<15} {'新文件名':<15} {'冲突级别'}\n"
    report_str += "-" * 60 + "\n"
    
    for src_path, info in report.items():
        report_str += f"{src_path:<40} {info['original_name']:<15} {info['new_name']:<15} {info['conflict_level']}\n"
    
    report_str += "-" * 60 + "\n"
    report_str += f"总计解决 {len(report)} 个文件名冲突"
    
    return report_str
  

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


def calculate_md5(filepath):
    """计算文件的MD5哈希值（支持大文件）"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, PermissionError):
        return None


def find_duplicate_files(directory):
    """查找并分组重复文件"""
    md5_groups = defaultdict(list)
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            md5 = calculate_md5(filepath)
            if md5:
                md5_groups[md5].append(filepath)
    
    return {k: v for k, v in md5_groups.items() if len(v) > 1}


def delete_duplicates(duplicates, simulate=False):
    """删除重复文件（保留每组第一个文件）"""
    deletion_log = []
    for md5, file_list in duplicates.items():
        # 按文件名排序确保一致性
        sorted_files = sorted(file_list)
        keeper = sorted_files[0]
        
        for filepath in sorted_files[1:]:
            if simulate:
                deletion_log.append(f"[SIMULATE] 将删除: {filepath} (保留 {keeper})")
            else:
                try:
                    os.remove(filepath)
                    deletion_log.append(f"已删除: {filepath} (保留 {keeper})")
                except Exception as e:
                    deletion_log.append(f"删除失败 {filepath}: {str(e)}")
    
    return deletion_log
  

def find_and_delete_duplicates(source_dir, simulate=False):
    if not os.path.isdir(source_dir):
        logger.info("错误: 目录不存在")
        return

    logger.info(f"扫描目录: {source_dir}")
    duplicates = find_duplicate_files(source_dir)
    
    if not duplicates:
        logger.info("✅ 未发现重复文件")
        return

    # 打印重复文件分组
    logger.info("发现重复文件组:")
    for i, (md5, files) in enumerate(duplicates.items(), 1):
        logger.info(f"组 #{i} (MD5: {md5}):")
        for f in sorted(files):
            logger.info(f"  - {os.path.basename(f)}")

    # 删除重复文件
    logger.info("处理重复文件...")
    log = delete_duplicates(duplicates, simulate=simulate)
    
    logger.info("操作日志:")
    for entry in log:
        logger.info(entry)
    
    logger.info(f"总计: 发现 {len(duplicates)} 组重复文件，已处理 {len(log)} 个重复项")


# 支持的图片和视频扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg', '.3gp', '.m4v'}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

#移动单个文件到指定目录，并解决文件名冲突的问题
def move_file_with_conflict_resolution(source_path, destination_path):
    """
    移动文件到指定目录，并解决文件名冲突
    参数:
        source_path (str): 源文件路径
        destination_path (str): 目标目录路径
    返回:
        bool: 移动是否成功
    """
    
    # 获取文件名和扩展名
    base_name, ext = os.path.splitext(os.path.basename(source_path))
    new_path = os.path.join(destination_path, base_name + ext)
    
    # 检查文件是否存在冲突
    counter = 1
    while os.path.exists(new_path):
        new_name = f"{base_name}_{counter}{ext}"
        new_path = os.path.join(destination_path, new_name)
        counter += 1
    
    # 移动文件
    try:
        shutil.move(source_path, new_path)
        logger.info(f"成功移动文件: {source_path} -> {new_path}")
        return True
    except Exception as e:
        logger.error(f"移动文件失败: {e}")
        return False


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


def get_video_datetime(filepath):
    """
    获取视频的拍摄时间
    返回格式: YYYY:MM:DD HH:MM:SS 或 None
    """
    try:
        # 使用exiftool获取视频元数据
        result = subprocess.run(
            ['exiftool', '-CreateDate', '-d', '%Y:%m:%d %H:%M:%S', '-T', filepath],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 处理输出结果
        output = result.stdout.strip()
        if output and output != '-':
            # 处理可能的异常格式
            clean_value = output.split('.')[0]  # 移除毫秒部分
            clean_value = clean_value[:19]  # 确保长度正确
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
            dt_str = get_exif_datetime(file_path)
            if dt_str:
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
        dt_str = get_exif_datetime(file_path)
        if not dt_str:
            continue
        # 如果filename 已经包括dst_str，则跳过
        dt_obj = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S").strftime('%Y%m%d_%H%M%S')
        if dt_obj in filename:
            logger.info(f"跳过重命名: {filename} 已符合命名规则, 拍摄时间: {dt_obj}")
            continue
            
        _, ext = os.path.splitext(filename)
        new_name = create_target_filename(dt_str, ext, os.listdir(camera_dir))
        
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
            
        if filename.startswith("IMG_") and len(filename) >= 12:
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
    photo_dir = os.path.join(source_path, "no_camera")
    
    if not os.path.exists(camera_dir):
        os.makedirs(camera_dir)
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)
    
    # 执行处理步骤
    classify_media(source_path, camera_dir, photo_dir)
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


def set_file_creation_date(filepath, dt_str):
    """
    设置文件的创建时间为指定的日期时间字符串（格式：%Y:%m:%d %H:%M:%S）
    参数:
        filepath: 文件路径
        dt_str: 日期时间字符串，格式为"%Y:%m:%d %H:%M:%S"
    """
    try:
        # 将字符串转换为datetime对象
        dt_obj = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        # 转换为时间戳
        timestamp = dt_obj.timestamp()
        # 修改文件的创建时间和修改时间
        os.utime(filepath, (timestamp, timestamp))
        logger.info(f"设置创建时间成功: {filepath} -> {dt_str}")
        return True
    except Exception as e:
        logger.error(f"设置创建时间失败: {filepath} - {str(e)}")
        return False


def set_creation_time_for_photos(directory):
    """
    递归遍历目录，为每张照片设置创建时间为拍摄时间
    """
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            # 检查文件扩展名是否为图片
            _, ext = os.path.splitext(filename)
            if ext.lower() not in IMAGE_EXTENSIONS:
                continue
            # 获取拍摄时间
            dt_str = get_exif_datetime(filepath)
            if dt_str:
                set_file_creation_date(filepath, dt_str)


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


if __name__ == "__main__":
    main()
