"""
重复文件处理工具模块
包含MD5计算、重复文件查找和删除等功能
"""

from collections import defaultdict
import os
import hashlib
import logging

logger = logging.getLogger(__name__)

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


def find_duplicate_files(directory, recursive=False):
    """查找并分组重复文件
    
    参数:
        directory: 要查找的目录
        recursive: 是否递归查找子文件夹，默认为False
    """
    md5_groups = defaultdict(list)
    
    if recursive:
        # 递归遍历所有子文件夹
        for root, _, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    md5 = calculate_md5(filepath)
                    if md5:
                        md5_groups[md5].append(filepath)
    else:
        # 只处理当前目录
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
  

def find_and_delete_duplicates(source_dir, simulate=False, recursive=False):
    """查找并删除重复文件"""
    if not os.path.isdir(source_dir):
        logger.info("错误: 目录不存在")
        return

    logger.info(f"扫描目录: {source_dir}")
    duplicates = find_duplicate_files(source_dir, recursive=recursive)
    
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
