# 把文件夹下面所有的文件拷贝到一个新目录，并解决文件命名冲突

import os
import shutil
from collections import defaultdict

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

    # 递归遍历源目录
    for root, _, files in os.walk(src_dir):
        for filename in files:
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
    
    return conflict_report

def print_conflict_report(report):
    """打印冲突解决报告"""
    if not report:
        print("✅ 未发生文件名冲突")
        return
    
    print("\n📊 文件名冲突解决报告:")
    print("-" * 60)
    print(f"{'源文件路径':<40} {'原文件名':<15} {'新文件名':<15} {'冲突级别'}")
    print("-" * 60)
    
    for src_path, info in report.items():
        print(f"{src_path:<40} {info['original_name']:<15} {info['new_name']:<15} {info['conflict_level']}")
    
    print("-" * 60)
    print(f"总计解决 {len(report)} 个文件名冲突")

if __name__ == "__main__":
    # 用户输入源目录和目标目录
    source_dir = input("请输入源目录路径: ").strip()
    dest_dir = input("请输入目标目录路径: ").strip()

    # 验证路径有效性
    if not os.path.isdir(source_dir):
        print("错误: 源目录不存在或不是目录")
        exit(1)
    
    print(f"\n开始复制文件: {source_dir} → {dest_dir}")
    report = copy_files_with_conflict_resolution(source_dir, dest_dir)
    
    print("\n操作完成! 文件复制统计:")
    print(f"源目录: {source_dir}")
    print(f"目标目录: {dest_dir}")
    print_conflict_report(report)
