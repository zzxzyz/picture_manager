import os
import re
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from collections import defaultdict
import sys

def get_shooting_time(file_path):
    """
    获取照片拍摄时间（优先使用EXIF元数据）
    
    参数:
        file_path (str): 照片文件路径
        
    返回:
        datetime对象: 拍摄时间
        str: 错误信息（成功则为None）
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
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S"), None
        
        # EXIF数据不存在则使用文件创建时间
        return (
            datetime.fromtimestamp(os.path.getctime(file_path)), 
            "警告: 使用文件创建时间代替拍摄时间"
        )
    
    except Exception as e:
        return None, f"错误: {str(e)}"

def generate_new_filename(file_path, time_counter):
    """
    生成新的文件名并处理冲突
    
    参数:
        file_path (str): 原始文件路径
        time_counter (dict): 时间戳使用计数器
        
    返回:
        str: 新文件路径
        str: 状态信息
    """
    try:
        # 获取文件信息
        dir_path = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # 获取拍摄时间
        shoot_time, error = get_shooting_time(file_path)
        if not shoot_time:
            return file_path, error
        
        # 格式化时间字符串
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
        new_path = os.path.join(dir_path, new_name)
        
        # 避免覆盖已存在文件
        conflict_count = 0
        while os.path.exists(new_path):
            conflict_count += 1
            new_name = f"IMG_{time_str}_{counter}_{conflict_count}{file_ext}"
            new_path = os.path.join(dir_path, new_name)
        
        return new_path, error
    
    except Exception as e:
        return file_path, f"处理错误: {str(e)}"

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
    
    # 遍历所有文件
    results = []
    for foldername, _, filenames in os.walk(root_dir):
        # 初始化时间戳计数器（每个文件夹独立计数）
        time_counter = defaultdict(int)
        
        for filename in filenames:
            if filename.lower().endswith(valid_exts):
                original_path = os.path.join(foldername, filename)
                new_path, status = generate_new_filename(original_path, time_counter)
                
                # 执行重命名
                if original_path != new_path:
                    try:
                        os.rename(original_path, new_path)
                        results.append({
                            "original": filename,
                            "new": os.path.basename(new_path),
                            "path": foldername,
                            "status": status or "成功"
                        })
                    except Exception as e:
                        results.append({
                            "original": filename,
                            "new": "未重命名",
                            "path": foldername,
                            "status": f"重命名失败: {str(e)}"
                        })
    
    return results

def print_summary_report(results):
    """打印整理报告"""
    if not results:
        print("\n🔍 未找到符合条件的照片文件")
        return
    
    print("\n📊 照片重命名结果报告:")
    print("=" * 70)
    print(f"{'原文件名':<25} {'新文件名':<25} {'状态':<20}")
    print("-" * 70)
    
    success_count = 0
    for item in results:
        status_icon = "✅" if "成功" in item["status"] else "❌"
        print(f"{item['original'][:24]:<25} {item['new'][:24]:<25} {status_icon} {item['status'][:20]}")
        if "成功" in item["status"]:
            success_count += 1
    
    print("=" * 70)
    print(f"总计处理: {len(results)} 个文件 | 成功: {success_count} | 失败: {len(results)-success_count}")
    print(f"详细路径: {os.path.abspath(results[0]['path'])}")

if __name__ == "__main__":
    print("📷 照片批量重命名工具")
    print("=" * 50)
    
    # 获取目标路径
    target_dir = input("请输入照片目录路径: ").strip()
    
    if not os.path.isdir(target_dir):
        print(f"\n❌ 错误: 目录不存在 - {target_dir}")
        sys.exit(1)
    
    # 执行批量重命名
    print("\n⏳ 正在处理照片，请稍候...")
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
