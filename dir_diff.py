import os
import hashlib
from collections import defaultdict
import argparse

def calculate_file_hash(filepath):
    """计算文件的MD5哈希值（支持大文件）"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, OSError):
        return None

def scan_folder(directory):
    """扫描文件夹并返回{哈希值: [文件名列表]}的映射"""
    content_map = defaultdict(list)
    for filename in os.listdir(directory):
        if filename == '.DS_Store':
            continue
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_hash = calculate_file_hash(filepath)
            if file_hash:
                content_map[file_hash].append(filename)
    return content_map

def compare_folders(dirA, dirB):
    """比较两个文件夹的文件内容"""
    # 扫描文件夹获取内容映射
    mapA = scan_folder(dirA)
    mapB = scan_folder(dirB)
    
    # 获取哈希值集合
    hashesA = set(mapA.keys())
    hashesB = set(mapB.keys())
    
    # 找出共同哈希值（内容相同的文件）
    common_hashes = hashesA & hashesB
    # 找出独有哈希值
    only_in_A = hashesA - hashesB
    only_in_B = hashesB - hashesA
    
    # 构建相同内容文件对应关系
    matched_pairs = []
    for hash_val in common_hashes:
        for fileA in mapA[hash_val]:
            for fileB in mapB[hash_val]:
                matched_pairs.append((fileA, fileB))
    
    # 构建独有文件列表
    unique_in_A = []
    for hash_val in only_in_A:
        unique_in_A.extend(mapA[hash_val])
    
    unique_in_B = []
    for hash_val in only_in_B:
        unique_in_B.extend(mapB[hash_val])
    
    return matched_pairs, unique_in_A, unique_in_B

def main():
    parser = argparse.ArgumentParser(description='比较两个文件夹的文件内容')
    parser.add_argument('dirA', help='第一个文件夹路径')
    parser.add_argument('dirB', help='第二个文件夹路径')
    args = parser.parse_args()
    
    if not os.path.isdir(args.dirA) or not os.path.isdir(args.dirB):
        print("错误: 输入的路径必须是有效的文件夹")
        return
    
    # 获取绝对路径并标准化
    dirA = os.path.abspath(args.dirA)
    dirB = os.path.abspath(args.dirB)
    
    matched_pairs, unique_in_A, unique_in_B = compare_folders(dirA, dirB)
    
    # 输出比较结果
    if not unique_in_A and not unique_in_B:
        print("全部一样")
    else:
        print("内容相同的文件:")
        for fileA, fileB in matched_pairs:
            print(f"  {dirA}/{fileA} ↔ {dirB}/{fileB}")
        
        if unique_in_A:
            print(f"\n{dirA} 中独有的文件:")
            for file in unique_in_A:
                print(f"  {file}")
        
        if unique_in_B:
            print(f"\n{dirB} 中独有的文件:")
            for file in unique_in_B:
                print(f"  {file}")

if __name__ == "__main__":
    main()