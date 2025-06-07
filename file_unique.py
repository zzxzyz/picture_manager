import os
import hashlib
import argparse
from collections import defaultdict

def calculate_md5(filepath):
    """计算文件的MD5哈希值（支持大文件）"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, PermissionError):
        return None

def find_duplicate_files(directory):
    """查找并分组重复文件"""
    md5_groups = defaultdict(list)
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            md5 = calculate_md5(filepath)
            if md5:
                md5_groups[md5].append(filepath)
    
    return {k: v for k, v in md5_groups.items() if len(v) > 1}

def delete_duplicates(duplicates, simulate=False):
    """删除重复文件（保留每组第一个文件）"""
    deletion_log = []
    for md5, file_list in duplicates.items():
        # 按文件名排序确保一致性
        sorted_files = sorted(file_list)
        keeper = sorted_files[0]
        
        for filepath in sorted_files[1:]:
            if simulate:
                deletion_log.append(f"[SIMULATE] 将删除: {filepath} (保留 {keeper})")
            else:
                try:
                    os.remove(filepath)
                    deletion_log.append(f"已删除: {filepath} (保留 {keeper})")
                except Exception as e:
                    deletion_log.append(f"删除失败 {filepath}: {str(e)}")
    
    return deletion_log

def main():
    parser = argparse.ArgumentParser(description="查找并删除重复文件")
    parser.add_argument("directory", help="要扫描的目录路径")
    parser.add_argument("--simulate", action="store_true", help="模拟运行（不实际删除）")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print("错误: 目录不存在")
        return

    print(f"扫描目录: {args.directory}")
    duplicates = find_duplicate_files(args.directory)
    
    if not duplicates:
        print("✅ 未发现重复文件")
        return

    # 打印重复文件分组
    print("\n发现重复文件组:")
    for i, (md5, files) in enumerate(duplicates.items(), 1):
        print(f"\n组 #{i} (MD5: {md5}):")
        for f in sorted(files):
            print(f"  - {os.path.basename(f)}")

    # 删除重复文件
    print("\n处理重复文件...")
    log = delete_duplicates(duplicates, args.simulate)
    
    print("\n操作日志:")
    for entry in log:
        print(entry)
    
    print(f"\n总计: 发现 {len(duplicates)} 组重复文件，已处理 {len(log)} 个重复项")

if __name__ == "__main__":
    main()