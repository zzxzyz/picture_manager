from collections import defaultdict
import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.FileHandler("photo_renamer.log"),
        logging.StreamHandler()
    ]
)

# 标准文件名模式: IMG_YYYYMMDD_HHMMSS.ext
STANDARD_NAME_PATTERN = re.compile(r'^IMG_\d{8}_\d{6}\.\w+$', re.IGNORECASE)

def is_standard_filename(filename):
    """检查文件名是否符合目标格式 IMG_YYYYMMDD_HHMMSS.ext"""
    return bool(STANDARD_NAME_PATTERN.match(filename))

def get_shooting_time(file_path):
    """
    获取照片拍摄时间（优先使用EXIF元数据）
    
    参数:
        file_path (Path): 照片文件路径
        
    返回:
        datetime对象: 拍摄时间 (成功时)
        None: 无法获取拍摄时间时
    """
    try:
        # 尝试从EXIF元数据获取拍摄时间
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    if tag_name == "DateTimeOriginal":
                        # 转换EXIF时间字符串为datetime对象
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        
        return None
    
    except (UnidentifiedImageError, TypeError, ValueError, OSError) as e:
        logging.warning(f"无法读取 {file_path.name} 的EXIF: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"处理 {file_path.name} 时发生意外错误: {str(e)}")
        return None

def generate_new_filename(file_path, time_counter):
    """
    生成新的文件名并处理冲突
    
    参数:
        file_path (Path): 原始文件路径
        time_counter (dict): 时间戳使用计数器
        
    返回:
        Path: 新文件路径
        str: 状态信息
    """
    # 获取文件信息
    dir_path = file_path.parent
    filename = file_path.name
    file_ext = file_path.suffix.lower()
    
    # 检查是否已经是标准文件名
    if is_standard_filename(filename):
        return file_path, "跳过 (已符合命名规则)"
    
    # 获取拍摄时间
    shoot_time = get_shooting_time(file_path)
    if not shoot_time:
        return file_path, "跳过 (无拍摄时间)"
    
    # 格式化时间字符串 (YYYYMMDD_HHMMSS)
    time_str = shoot_time.strftime("%Y%m%d_%H%M%S")
    base_name = f"IMG_{time_str}{file_ext}"
    
    # 处理文件名冲突
    counter = time_counter[time_str]
    if counter > 0:
        new_name = f"IMG_{time_str}_{counter}{file_ext}"
    else:
        new_name = base_name
    
    # 更新计数器
    time_counter[time_str] += 1
    
    # 构造新路径
    new_path = dir_path / new_name
    
    # 避免覆盖已存在文件
    conflict_count = 0
    while new_path.exists():
        conflict_count += 1
        new_name = f"IMG_{time_str}_{counter}_{conflict_count}{file_ext}"
        new_path = dir_path / new_name
    
    # 检查是否有必要重命名（新名称与旧名称相同）
    if new_path == file_path:
        return file_path, "跳过 (名称无变化)"
    
    return new_path, "成功"

def batch_rename_photos(root_dir):
    """
    批量重命名照片文件
    
    参数:
        root_dir (str): 根目录路径
        
    返回:
        list: 重命名结果报告
    """
    # 支持的图片格式
    valid_exts = ('.jpg', '.jpeg', '.png', '.heic', '.gif', '.tiff', '.webp', '.bmp')
    
    # 第一阶段：收集所有图片文件
    all_images = []
    root_path = Path(root_dir).resolve()
    
    logging.info("开始扫描文件夹...")
    for foldername, _, filenames in os.walk(root_path):
        folder_path = Path(foldername)
        for filename in filenames:
            file_path = folder_path / filename
            if file_path.suffix.lower() in valid_exts:
                all_images.append(file_path)
    
    total_count = len(all_images)
    if total_count == 0:
        return []
    
    logging.info(f"找到 {total_count} 张照片文件")
    
    # 第二阶段：按文件夹分组处理文件
    folder_groups = defaultdict(list)
    for file_path in all_images:
        folder_groups[file_path.parent].append(file_path)
    
    # 第三阶段：处理文件重命名
    results = []
    processed_count = 0
    
    for folder_path, file_list in folder_groups.items():
        # 初始化时间戳计数器（每个文件夹独立计数）
        time_counter = defaultdict(int)
        
        for file_path in file_list:
            # 生成新文件名
            new_path, status = generate_new_filename(file_path, time_counter)
            
            # 跳过不需要重命名的文件
            if file_path == new_path:
                results.append({
                    "original": file_path.name,
                    "new": file_path.name,
                    "path": str(file_path.parent),
                    "status": status
                })
                continue
            
            # 执行重命名
            try:
                file_path.rename(new_path)
                results.append({
                    "original": file_path.name,
                    "new": new_path.name,
                    "path": str(file_path.parent),
                    "status": status
                })
                processed_count += 1
                logging.info(f"重命名: {file_path.name} → {new_path.name}")
            except Exception as e:
                error_msg = f"重命名失败: {str(e)}"
                results.append({
                    "original": file_path.name,
                    "new": file_path.name,
                    "path": str(file_path.parent),
                    "status": error_msg
                })
                logging.error(error_msg)
    
    logging.info(f"处理完成! 共处理 {len(results)} 个文件，其中 {processed_count} 个文件被重命名")
    return results

def print_summary_report(results):
    """打印整理报告"""
    if not results:
        print("\n🔍 未找到符合条件的照片文件")
        return
    
    print("\n📊 照片重命名结果报告:")
    print("=" * 70)
    print(f"{'原文件名':<30} {'新文件名':<30} {'状态'}")
    print("-" * 70)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for item in results:
        # 状态分类统计
        if "成功" in item["status"]:
            status_icon = "✅"
            success_count += 1
        elif "跳过" in item["status"]:
            status_icon = "↷"
            skip_count += 1
        else:
            status_icon = "❌"
            error_count += 1
        
        print(f"{item['original'][:28]:<30} {item['new'][:28]:<30} {status_icon} {item['status']}")
    
    print("=" * 70)
    print(f"总计: {len(results)} 个文件")
    print(f"✅ 成功重命名: {success_count}")
    print(f"↷ 跳过: {skip_count} (符合规则、无变化或无拍摄时间)")
    print(f"❌ 失败: {error_count}")
    
    if results:
        print(f"处理路径: {os.path.abspath(results[0]['path'])}")

if __name__ == "__main__":
    print("📷 照片批量重命名工具")
    print("=" * 50)
    print("命名规则: IMG_日期_时间.后缀名 (如 IMG_20131221_214348.jpg)")
    print("=" * 50)
    
    # 获取目标路径
    target_dir = input("请输入照片目录路径: ").strip()
    
    if not os.path.isdir(target_dir):
        print(f"\n❌ 错误: 目录不存在 - {target_dir}")
        sys.exit(1)
    
    # 执行批量重命名
    print("\n⏳ 正在扫描并处理照片，请稍候...")
    rename_results = batch_rename_photos(target_dir)
    
    # 显示结果
    print("\n" + "=" * 50)
    print("✨ 处理完成! 结果摘要")
    print("=" * 50)
    print_summary_report(rename_results)
    
    # 显示示例
    if rename_results:
        sample = next((r for r in rename_results if "成功" in r["status"]), None)
        if sample:
            print(f"\n示例: {sample['original']} → {sample['new']}")

# /Users/zhengjunming/Documents/mj_picture/DCIM/image/camera_01/20170819_IMG_2092.JPG
