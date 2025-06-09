import os
import re
import argparse
import logging
import shutil
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS

# 配置日志
logging.basicConfig(
    filename='photo_organizer.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_shooting_time(file_path):
    """获取照片拍摄时间，处理异常格式"""
    try:
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
                                logging.warning(f"无法解析 {file_path} 的拍摄时间: {value}")
                                return None
        return None
    except (UnidentifiedImageError, TypeError, ValueError, OSError) as e:
        logging.warning(f"无法读取 {file_path} 的EXIF: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"处理 {file_path} 时发生意外错误: {str(e)}")
        return None

def process_photos(root_dir):
    """处理照片：分类、重命名、按年份分组"""
    # 创建分类目录
    camera_dir = os.path.join(root_dir, 'camera')
    photo_dir = os.path.join(root_dir, 'photo')
    os.makedirs(camera_dir, exist_ok=True)
    os.makedirs(photo_dir, exist_ok=True)
    
    # 收集所有照片文件
    photo_files = []
    for root, _, files in os.walk(root_dir):
        # 跳过分类目录
        if root in [camera_dir, photo_dir]:
            continue
            
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')):
                photo_files.append(os.path.join(root, file))
    
    # 处理每张照片
    for file_path in photo_files:
        try:
            shooting_time = get_shooting_time(file_path)
            
            if shooting_time:
                # 移动到camera目录
                dest_dir = camera_dir
                
                # 生成新文件名
                time_str = shooting_time.strftime("%Y%m%d_%H%M%S")
                ext = os.path.splitext(file_path)[1].lower()
                new_name = f"IMG_{time_str}{ext}"
                new_path = os.path.join(camera_dir, new_name)
                
                # 处理文件名冲突
                counter = 1
                while os.path.exists(new_path):
                    new_name = f"IMG_{time_str}_{counter}{ext}"
                    new_path = os.path.join(camera_dir, new_name)
                    counter += 1
                
                # 重命名文件（如果需要）
                if os.path.basename(file_path) != new_name:
                    shutil.move(file_path, new_path)
                    logging.info(f"重命名并移动: {os.path.basename(file_path)} -> {new_name}")
                else:
                    shutil.move(file_path, new_path)
                    logging.info(f"移动: {os.path.basename(file_path)}")
                
                # 按年份分组
                year_dir = os.path.join(camera_dir, str(shooting_time.year))
                os.makedirs(year_dir, exist_ok=True)
                final_path = os.path.join(year_dir, new_name)
                
                # 处理目标文件已存在的情况
                if os.path.exists(final_path):
                    logging.warning(f"文件已存在，跳过: {final_path}")
                else:
                    shutil.move(new_path, final_path)
                    logging.info(f"按年份分组: {new_name} -> {year_dir}")
                
            else:
                # 移动到photo目录
                dest_path = os.path.join(photo_dir, os.path.basename(file_path))
                shutil.move(file_path, dest_path)
                logging.info(f"移动无时间照片: {os.path.basename(file_path)} -> photo")
                
        except Exception as e:
            logging.error(f"处理 {file_path} 失败: {str(e)}")
    
    logging.info("照片整理完成")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='整理照片：按拍摄时间分类、重命名和分组')
    parser.add_argument('directory', help='要处理的目录路径')
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        logging.error(f"目录不存在: {args.directory}")
        exit(1)
        
    process_photos(args.directory)
