"""
文件操作工具模块
包含文件复制、移动、冲突解决等功能
"""

from collections import defaultdict
from datetime import datetime
import os
import shutil
import logging

logger = logging.getLogger(__name__)

def copy_files_with_unique_name(source_dir, target_dir, file_types=None):
    """
    递归复制所有文件到目标目录，解决文件名冲突
    
    :param source_dir: 源目录
    :param target_dir: 目标目录
    :param file_types: 允许的文件扩展名列表（例如 ['.jpg', '.png']），如果为空或None则不过滤
    """
    # 创建目标目录（如果不存在）
    os.makedirs(target_dir, exist_ok=True)
    conflict_report = {}

    # 递归遍历源目录
    for root, _, files in os.walk(source_dir):
        for filename in files:
            base_name, ext = os.path.splitext(filename)
            ext = ext.lower()
            if file_types and ext not in file_types:
                continue
            
            file_fullpath = os.path.join(root, filename)
            new_path, conflict_level = move_file_with_unique_name(file_fullpath, target_dir, is_copy=True)
            
            # 记录冲突解决情况
            if conflict_level > 0:
                conflict_report[file_fullpath] = {
                    "original_name": filename,
                    "new_name": new_path,
                    "conflict_level": conflict_level
                }
    return conflict_report


def generate_conflict_report(report):
    """
    生成文件名冲突解决报告
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


def move_file_with_unique_name(file_fullpath, target_dir, is_copy=False):
    """
    移动或复制指定文件到指定目录，并解决文件名冲突
    """
    # 获取文件名和扩展名
    base_name, ext = os.path.splitext(os.path.basename(file_fullpath))
    new_name = base_name + ext
    new_path = os.path.join(target_dir, new_name)
    
    # 检查文件是否存在冲突
    counter = 0
    while os.path.exists(new_path):
        counter += 1
        new_name = f"{base_name}_{counter}{ext}"
        new_path = os.path.join(target_dir, new_name)
    
    # 移动文件
    try:
        if is_copy:
            shutil.copy2(file_fullpath, new_path)
            logger.info(f"复制文件: {file_fullpath} -> {new_path}")
        else:
          shutil.move(file_fullpath, new_path)
          logger.info(f"移动文件: {file_fullpath} -> {new_path}")
        return new_path, counter,
    except Exception as e:
        logger.error(f"操作文件失败: {e} is_copy: {is_copy}")
        return None, counter,
