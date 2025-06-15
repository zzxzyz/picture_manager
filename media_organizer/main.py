#!/usr/bin/env python3
"""
媒体文件整理主程序
"""
import argparse
import logging
from .file_utils import collect_media_files, copy_with_conflict_resolution, deduplicate_directory
from .media_processor import process_images, process_videos

# 配置日志
logging.basicConfig(
    filename='organizer.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='整理图片和视频文件')
    parser.add_argument('source_dir', help='源目录路径')
    parser.add_argument('target_dir', help='目标目录路径')
    args = parser.parse_args()

    try:
        logger.info(f"开始整理: 源目录={args.source_dir}, 目标目录={args.target_dir}")
        
        # 1. 收集并复制媒体文件
        image_files = collect_media_files(args.source_dir, ['jpg', 'jpeg', 'png', 'gif'])
        video_files = collect_media_files(args.source_dir, ['mp4', 'mov', 'avi', 'mkv'])
        
        copy_with_conflict_resolution(image_files, args.target_dir, 'images')
        copy_with_conflict_resolution(video_files, args.target_dir, 'videos')
        
        # 2. 去重
        deduplicate_directory(args.target_dir)
        
        # 3. 处理图片
        process_images(args.target_dir)
        
        # 4. 处理视频
        process_videos(args.target_dir)
        
        logger.info("文件整理完成")
    except Exception as e:
        logger.exception(f"处理过程中发生错误: {str(e)}")
        print(f"错误发生，详情请查看日志: organizer.log")

if __name__ == "__main__":
    main()
