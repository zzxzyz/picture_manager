#!/usr/bin/env python3
"""
照片整理工具
功能：
1. 读取照片拍摄时间并分类到camera/photo目录
2. 重命名照片为IMG_日期_时间格式
3. 按年份分组照片
"""

import argparse
from collections import defaultdict
import hashlib
import logging
import shutil
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
            dest_name = filename
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
    """生成冲突解决报告"""
    if not report:
        return "✅ 未发生文件名冲突\n"
    
    report_str = "\n📊 文件名冲突解决报告:\n"
    report_str += "-" * 60 + "\n"
    report_str += f"{'源文件路径':<40} {'原文件名':<15} {'新文件名':<15} {'冲突级别'}\n"
    report_str += "-" * 60 + "\n"
    
    for src_path, info in report.items():
        report_str += f"{src_path:<40} {info['original_name']:<15} {info['new_name']:<15} {info['conflict_level']}\n"
    
    report_str += "-" * 60 + "\n"
    report_str += f"总计解决 {len(report)} 个文件名冲突\n"
    
    return report_str
  

def mere_all_files(source_dir: str, dest_dir: str):
      # 验证路径有效性
    if not os.path.isdir(source_dir):
        logger.error("错误: 源目录不存在或不是目录")
        exit(1)
    
    logger.info(f"\n开始复制文件: {source_dir} → {dest_dir}")
    report = copy_files_with_conflict_resolution(source_dir, dest_dir)
    
    # 生成并记录报告
    report_str = generate_conflict_report(report)
    logger.info("\n操作完成! 文件复制统计:")
    logger.info(f"源目录: {source_dir}")
    logger.info(f"目标目录: {dest_dir}")
    logger.info(report_str)
    
    # 同时在控制台输出报告
    print("\n操作完成! 详细日志已保存到 merge_all.log")
    print(report_str)


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
        print("错误: 目录不存在")
        return

    print(f"扫描目录: {source_dir}")
    duplicates = find_duplicate_files(source_dir)
    
    if not duplicates:
        print("✅ 未发现重复文件")
        return

    # 打印重复文件分组
    print("\n发现重复文件组:")
    for i, (md5, files) in enumerate(duplicates.items(), 1):
        print(f"\n组 #{i} (MD5: {md5}):")
        for f in sorted(files):
            print(f"  - {os.path.basename(f)}")

    # 删除重复文件
    print("\n处理重复文件...")
    log = delete_duplicates(duplicates, simulate=simulate)
    
    print("\n操作日志:")
    for entry in log:
        print(entry)
    
    print(f"\n总计: 发现 {len(duplicates)} 组重复文件，已处理 {len(log)} 个重复项")


# 支持的图片和视频扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg'}

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
            dest = os.path.join(image_dir, filename)
            shutil.move(filepath, dest)
            print(f"移动图片: {filename} -> image/")
            
        elif ext in VIDEO_EXTENSIONS:
            dest = os.path.join(video_dir, filename)
            shutil.move(filepath, dest)
            print(f"移动视频: {filename} -> video/")
            
        else:
            print(f"保留文件: {filename}")

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
    
    
def classify_and_rename_photos(source_path):
    """
    步骤1: 分类照片到camera和photo目录
    """
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
    
    # 删除所有重复文件
    logger.info(f"删除所有重复文件: {target_path}")
    find_and_delete_duplicates(target_path)
    
    # 分类文件
    logger.info(f"分类文件: {target_path}")
    classify_files(target_path)
    
    # 分类和重命名文件
    image_path = os.path.join(target_path, "image")
    logger.info(f"分类和重命名文件: {image_path}")
    classify_and_rename_photos(image_path)


if __name__ == "__main__":
    main()
