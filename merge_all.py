# 把文件夹下面所有的文件拷贝到一个新目录，并解决文件命名冲突
# 已验证OK

import os
import shutil
import logging
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('merge_all.log'),
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
  

def mere_all(source_dir: str, dest_dir: str):
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


if __name__ == "__main__":
    # 用户输入源目录和目标目录
    source_dir = input("请输入源目录路径: ").strip()
    dest_dir = input("请输入目标目录路径: ").strip()
    mere_all(source_dir, dest_dir)
