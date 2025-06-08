# 查找处所有同名文件，并比较内容是否相同
import os
import hashlib
from collections import defaultdict

def get_file_hash(file_path, block_size=65536):
    """计算文件的MD5哈希值（大文件友好）"""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(block_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"无法读取文件 {file_path}: {str(e)}")
        return None

def find_and_compare_duplicates(start_dir):
    """主函数：查找并比较同名文件"""
    # 1. 递归收集所有文件路径
    file_map = defaultdict(list)
    for root, _, files in os.walk(start_dir):
        for filename in files:
            full_path = os.path.join(root, filename)
            file_map[filename].append(full_path)

    # 2. 筛选出同名文件组
    duplicate_groups = {k: v for k, v in file_map.items() if len(v) > 1}
    
    # 3. 比较同名文件内容
    results = {}
    for filename, paths in duplicate_groups.items():
        content_groups = defaultdict(list)
        for path in paths:
            file_hash = get_file_hash(path)
            if file_hash:
                content_groups[file_hash].append(path)
        results[filename] = content_groups
    
    return results

def print_results(comparison_results):
    """格式化输出比较结果"""
    for filename, content_groups in comparison_results.items():
        print(f"\n📁 文件名: {filename}")
        print(f"🔍 发现 {len(content_groups)} 个不同的内容版本")
        
        for idx, (file_hash, paths) in enumerate(content_groups.items(), 1):
            status = "✅ 内容相同" if len(paths) > 1 else "⚠️ 唯一内容"
            print(f"\n  版本组 #{idx} ({status})")
            print(f"  🪪 哈希值: {file_hash}")
            
            for path in paths:
                file_size = os.path.getsize(path)
                print(f"    • {path} (大小: {file_size}字节)")

if __name__ == "__main__":
    start_directory = input("请输入要扫描的目录路径: ")
    
    if not os.path.isdir(start_directory):
        print("错误: 指定的路径不是目录")
    else:
        print(f"\n开始扫描目录: {start_directory}")
        results = find_and_compare_duplicates(start_directory)
        
        if not results:
            print("\n🎉 未发现任何同名文件")
        else:
            print_results(results)
