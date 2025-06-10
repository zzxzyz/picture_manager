import argparse
import logging
import sys
from file_organizer import FileOrganizer


def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='整理图片和视频文件')
    parser.add_argument('source_folder', help='源文件夹路径')
    parser.add_argument('target_folder', help='目标文件夹路径')
    args = parser.parse_args()
    
    # 验证路径
    if not os.path.isdir(args.source_folder):
        print(f"错误: 源文件夹不存在 - {args.source_folder}")
        sys.exit(1)
    
    # 创建整理器实例
    organizer = FileOrganizer(args.source_folder, args.target_folder)
    
    # 执行整理流程
    try:
        success = organizer.organize()
        if success:
            print("文件整理完成!")
            sys.exit(0)
        else:
            print("整理过程中出现错误，请查看日志文件")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)


if __name__ == "__main__":
    main()
