# 把照片分类为有拍摄时间和无拍摄时间两类，有拍摄时间的放在camera目录下，无拍摄时间的放在photo目录下

import os
import shutil
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
import logging
from datetime import datetime
import re  # 添加正则表达式模块

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
                        # 清理时间字符串中的非法字符
                        clean_value = re.sub(r"[^0-9: ]", "", value)
                        
                        # 尝试解析时间
                        try:
                            return datetime.strptime(clean_value[:19], "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            # 尝试其他可能的格式
                            try:
                                return datetime.strptime(clean_value[:10], "%Y:%m:%d")
                            except ValueError:
                                logging.warning(f"无法解析 {file_path.name} 的拍摄时间: {value}")
                                return None
        
        return None
    
    except (UnidentifiedImageError, TypeError, ValueError, OSError) as e:
        logging.warning(f"无法读取 {file_path.name} 的EXIF: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"处理 {file_path.name} 时发生意外错误: {str(e)}")
        return None

def classify_photos(source_dir):
    """主分类函数：递归遍历并分类照片"""
    source_path = Path(source_dir).resolve()
    camera_dir = source_path / "camera"
    photo_dir = source_path / "photo"
    
    # 创建目标目录
    camera_dir.mkdir(exist_ok=True)
    photo_dir.mkdir(exist_ok=True)
    
    # 支持的图片格式
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.heic'}
    processed_count = 0
    error_count = 0
    
    # 递归遍历文件夹
    for root, _, files in os.walk(source_path):
        current_dir = Path(root)
        
        # 跳过目标目录
        if current_dir in [camera_dir, photo_dir]:
            continue
            
        for file in files:
            file_path = current_dir / file
            ext = file_path.suffix.lower()
            
            if ext not in image_exts:
                continue
                
            try:
                # 获取拍摄时间并打印
                shoot_time = get_shooting_time(file_path)
                time_str = shoot_time if shoot_time else "无拍摄时间"
                print(f"{file_path.name} | 拍摄时间: {time_str}")
                
                # 确定目标目录
                if shoot_time:
                    dest_base = camera_dir
                else:
                    dest_base = photo_dir
                
                # 保持相对路径结构
                relative_path = file_path.relative_to(source_path)
                dest_path = dest_base / relative_path
                
                # 创建目标目录并移动文件
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(dest_path))
                processed_count += 1
                
            except Exception as e:
                logging.error(f"处理 {file_path} 失败: {str(e)}")
                error_count += 1
    
    # 输出统计结果
    print(f"\n{'='*40}")
    print(f"处理完成! 共处理 {processed_count} 张照片")
    print(f"· 含拍摄时间: {len(list(camera_dir.rglob('*.*')))} 张 → camera/")
    print(f"· 无拍摄时间: {len(list(photo_dir.rglob('*.*')))} 张 → photo/")
    if error_count > 0:
        print(f"⚠ 失败: {error_count} 张 (详见日志)")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s]: %(message)s",
        filename="photo_classifier.log"
    )
    
    # 用户输入处理
    source_dir = input("请输入照片文件夹路径: ").strip()
    
    if not Path(source_dir).exists():
        print("错误: 路径不存在!")
    else:
        classify_photos(source_dir)
