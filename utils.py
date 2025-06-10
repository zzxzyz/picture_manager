import os
import hashlib
import shutil
from datetime import datetime
import exifread


def calculate_md5(file_path):
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_creation_time(file_path):
    """获取文件的拍摄时间或创建时间"""
    try:
        # 尝试从EXIF数据获取拍摄时间
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal')
            if 'EXIF DateTimeOriginal' in tags:
                dt = tags['EXIF DateTimeOriginal']
                return datetime.strptime(str(dt), '%Y:%m:%d %H:%M:%S')
    except:
        pass
    
    # 使用文件修改时间作为后备
    return datetime.fromtimestamp(os.path.getmtime(file_path))


def safe_copy(src, dst):
    """安全复制文件，避免覆盖同名文件"""
    if not os.path.exists(dst):
        os.makedirs(dst)
    
    base, ext = os.path.splitext(os.path.basename(src))
    counter = 1
    new_path = os.path.join(dst, f"{base}{ext}")
    
    while os.path.exists(new_path):
        new_path = os.path.join(dst, f"{base}_{counter}{ext}")
        counter += 1
    
    shutil.copy2(src, new_path)
    return new_path


def format_time(dt, format_str):
    """格式化时间对象为字符串"""
    return dt.strftime(format_str)


def extract_time_from_filename(filename):
    """尝试从文件名中提取时间信息"""
    # 实现将从文件名中提取时间的逻辑
    # 返回datetime对象或None
    return None
