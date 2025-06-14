"""
重复文件处理工具模块
包含MD5计算、重复文件查找和删除等功能
"""

import os
import hashlib
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def calculate_md5(filepath: str) -> Optional[str]:
    """
    计算文件的MD5哈希值（支持大文件）
    
    Args:
        filepath: 文件路径
        
    Returns:
        str: MD5哈希值，如果计算失败则返回None
        
    Raises:
        FileNotFoundError: 如果文件不存在
        PermissionError: 如果文件不可读
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")
    if not os.access(filepath, os.R_OK):
        raise PermissionError(f"文件不可读: {filepath}")
    
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"计算MD5失败: {filepath}, 错误: {e}")
        return None


def find_duplicate_files(directory: str, file_types: Optional[List[str]] = None, 
                        recursive: bool = False) -> Dict[str, List[str]]:
    """
    查找并分组重复文件
    
    Args:
        directory: 要查找的目录
        file_types: 允许的文件扩展名列表（例如 ['.jpg', '.png']），如果为空则处理所有文件
        recursive: 是否递归查找子文件夹
        
    Returns:
        Dict[str, List[str]]: 重复文件分组字典，键为MD5值，值为文件路径列表
        
    Raises:
        FileNotFoundError: 如果目录不存在
        PermissionError: 如果目录不可读
    """
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"目录不存在: {directory}")
    if not os.access(directory, os.R_OK):
        raise PermissionError(f"目录不可读: {directory}")
    
    md5_groups = {}
    
    # 定义文件遍历函数
    def process_file(filepath: str):
        if not os.path.isfile(filepath):
            return
            
        # 检查文件类型
        _, ext = os.path.splitext(filepath)
        if file_types and ext.lower() not in file_types:
            return
            
        # 计算MD5
        md5 = calculate_md5(filepath)
        if md5:
            if md5 not in md5_groups:
                md5_groups[md5] = []
            md5_groups[md5].append(filepath)
    
    # 遍历文件
    if recursive:
        for root, _, files in os.walk(directory):
            for filename in files:
                process_file(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            process_file(os.path.join(directory, filename))
    
    # 过滤出重复文件组
    return {k: v for k, v in md5_groups.items() if len(v) > 1}


def delete_duplicates(duplicates: Dict[str, List[str]], simulate: bool = False) -> List[str]:
    """
    删除重复文件（保留每组第一个文件）
    
    Args:
        duplicates: 重复文件分组字典
        simulate: 是否模拟操作（不实际删除文件）
        
    Returns:
        List[str]: 操作日志列表
        
    Raises:
        ValueError: 如果输入不是有效的重复文件字典
    """
    if not isinstance(duplicates, dict):
        raise ValueError("无效的重复文件字典")
        
    deletion_log = []
    for md5, file_list in duplicates.items():
        # 按文件路径排序确保一致性
        sorted_files = sorted(file_list)
        keeper = sorted_files[0]
        
        for filepath in sorted_files[1:]:
            if simulate:
                deletion_log.append(f"[模拟] 将删除: {filepath} (保留 {keeper})")
            else:
                try:
                    os.remove(filepath)
                    deletion_log.append(f"已删除: {filepath} (保留 {keeper})")
                except Exception as e:
                    deletion_log.append(f"删除失败 {filepath}: {str(e)}")
    
    return deletion_log
  

def find_and_delete_duplicates(source_dir: str, simulate: bool = False, 
                              recursive: bool = False, file_types: Optional[List[str]] = None) -> None:
    """
    查找并删除重复文件
    
    Args:
        source_dir: 源目录路径
        simulate: 是否模拟操作（不实际删除文件）
        recursive: 是否递归查找子文件夹
        file_types: 允许的文件扩展名列表
        
    Raises:
        FileNotFoundError: 如果源目录不存在
    """
    try:
        if not os.path.isdir(source_dir):
            raise FileNotFoundError(f"目录不存在: {source_dir}")

        logger.info(f"扫描目录: {source_dir}")
        duplicates = find_duplicate_files(source_dir, file_types, recursive)
        
        if not duplicates:
            logger.info("✅ 未发现重复文件")
            return

        # 打印重复文件分组
        logger.info(f"发现 {len(duplicates)} 组重复文件:")
        for i, (md5, files) in enumerate(duplicates.items(), 1):
            logger.info(f"组 #{i} (MD5: {md5[:8]}...):")
            for f in sorted(files):
                logger.info(f"  - {os.path.basename(f)}")

        # 删除重复文件
        logger.info("处理重复文件...")
        log_entries = delete_duplicates(duplicates, simulate)
        
        logger.info("操作日志:")
        for entry in log_entries:
            logger.info(entry)
        
        logger.info(f"总计处理: {len(log_entries)} 个重复文件")
    except Exception as e:
        logger.error(f"处理重复文件失败: {e}")
        raise
