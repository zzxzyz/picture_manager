import os
import shutil

# 支持的图片和视频扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg'}

def classify_files(directory):
    """
    分类目录中的文件：
    - 图片移动到image目录
    - 视频移动到video目录
    - 其他文件保留在根目录
    """
    # 创建目标目录
    image_dir = os.path.join(directory, 'image')
    video_dir = os.path.join(directory, 'video')
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)
    
    # 遍历目录中的文件
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # 跳过目录
        if os.path.isdir(filepath):
            continue
            
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # 分类文件
        if ext in IMAGE_EXTENSIONS:
            dest = os.path.join(image_dir, filename)
            shutil.move(filepath, dest)
            print(f"移动图片: {filename} -> image/")
            
        elif ext in VIDEO_EXTENSIONS:
            dest = os.path.join(video_dir, filename)
            shutil.move(filepath, dest)
            print(f"移动视频: {filename} -> video/")
            
        else:
            print(f"保留文件: {filename}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='分类文件到image和video目录')
    parser.add_argument('directory', help='要分类的目录路径')
    args = parser.parse_args()
    classify_files(args.directory)
