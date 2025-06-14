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

def copy_files_with_conflict_resolution(src_dir, dest_dir, file_types=None):
    """
    递归复制所有文件到目标目录，解决文件名冲突
    
    :param src_dir: 源目录
    :param dest_dir: 目标目录
    :param file_types: 允许的文件扩展名列表（例如 ['.jpg', '.png']），如果为空或None则不过滤
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
            base_name, ext = os.path.splitext(filename)
            ext = ext.lower()
            if file_types and ext not in file_types:
                continue
            src_path = os.path.join(root, filename)
            
            # 生成基本目标路径
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


def move_file_with_conflict_resolution(source_path, destination_path):
    """
    移动文件到指定目录，并解决文件名冲突
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
