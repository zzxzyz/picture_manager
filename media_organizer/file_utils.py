"""
文件操作工具模块
"""
import os
import shutil
import hashlib
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

def collect_media_files(directory, extensions):
    """
    递归收集指定扩展名的媒体文件
    
    :param directory: 要搜索的目录
    :param extensions: 文件扩展名列表，如['jpg', 'png']
    :return: 文件路径列表
    """
    media_files = []
    extensions = [ext.lower() for ext in extensions]
    
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1][1:].lower() in extensions:
                media_files.append(os.path.join(root, file))
    
    logger.info(f"在 {directory} 中找到 {len(media_files)} 个媒体文件")
    return media_files

def copy_with_conflict_resolution(files, target_dir, subdir):
    """
    复制文件到目标子目录，处理文件名冲突
    
    :param files: 要复制的文件列表
    :param target_dir: 目标目录
    :param subdir: 目标子目录
    """
    dest_dir = os.path.join(target_dir, subdir)
    os.makedirs(dest_dir, exist_ok=True)
    
    for src_path in files:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(dest_dir, filename)
        
        # 处理文件名冲突
        counter = 1
        while os.path.exists(dest_path):
            name, ext = os.path.splitext(filename)
            dest_path = os.path.join(dest_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        shutil.copy2(src_path, dest_path)
        logger.info(f"复制: {src_path} -> {dest_path}")

def calculate_md5(file_path):
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def deduplicate_directory(directory):
    """
    基于MD5哈希值删除重复文件
    
    :param directory: 要处理的目录
    """
    md5_dict = defaultdict(list)
    
    # 收集所有文件的MD5
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_md5 = calculate_md5(file_path)
            md5_dict[file_md5].append(file_path)
    
    # 删除重复文件
    duplicates_removed = 0
    for md5_value, paths in md5_dict.items():
        if len(paths) > 1:
            # 保留第一个文件，删除其他重复文件
            for path in paths[1:]:
                os.remove(path)
                logger.info(f"删除重复文件: {path}")
                duplicates_removed += 1
    
    logger.info(f"在 {directory} 中删除了 {duplicates_removed} 个重复文件")
