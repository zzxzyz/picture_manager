import os
import shutil
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import logging
from datetime import datetime

def get_shoot_time(image_path):
    """提取照片拍摄时间（EXIF DateTimeOriginal）"""
    try:
        with Image.open(image_path) as img:
            exif_data = img.getexif()
            
            # 检查是否存在EXIF数据
            if exif_data is None:
                return None
                
            # 检查原始拍摄时间标签（36867）
            if 36867 in exif_data:
                return exif_data[36867]
                
            # 检查其他可能的时间标签
            for tag in [306, 36868]:  # DateTime（306）和DateTimeDigitized（36868）
                if tag in exif_data:
                    return exif_data[tag]
                    
        return None
    except (UnidentifiedImageError, TypeError, ValueError, OSError) as e:
        logging.warning(f"无法读取 {image_path} 的EXIF: {str(e)}")
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
                shoot_time = get_shoot_time(file_path)
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
