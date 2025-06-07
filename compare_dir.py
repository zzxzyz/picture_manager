import os
import hashlib
import argparse
from collections import defaultdict

def calculate_md5(file_path):
    """计算文件的MD5值（支持大文件和错误处理）"""
    # 先获取文件大小，快速筛选不同文件
    try:
        file_size = os.path.getsize(file_path)
    except OSError:
        return None, 0
    
    md5_hash = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest(), file_size
    except (IOError, PermissionError, OSError):
        return None, file_size

def scan_folder(folder_path):
    """递归扫描文件夹并返回{MD5值: 文件路径列表}映射"""
    md5_map = defaultdict(list)
    base_path = os.path.abspath(folder_path)
    
    for root, _, files in os.walk(folder_path):
        for filename in files:
            abs_path = os.path.join(root, filename)
            # 跳过符号链接
            if os.path.islink(abs_path):
                continue
                
            rel_path = os.path.relpath(abs_path, base_path)
            md5, size = calculate_md5(abs_path)
            
            if md5:
                md5_map[md5].append(rel_path)
    
    return md5_map

def compare_folders(folder_a, folder_b):
    """比较两个文件夹的文件差异"""
    # 扫描两个文件夹
    map_a = scan_folder(folder_a)
    map_b = scan_folder(folder_b)
    
    # 获取所有唯一MD5值
    all_md5 = set(map_a.keys()) | set(map_b.keys())
    
    # 分类差异
    results = {
        'only_in_a': [],    # (相对路径, MD5)
        'only_in_b': [],    # (相对路径, MD5)
        'content_diff': []  # (相对路径, MD5_A, MD5_B)
    }
    
    for md5 in all_md5:
        files_a = map_a.get(md5, [])
        files_b = map_b.get(md5, [])
        
        # 处理仅存在于一侧的文件
        if not files_a:
            for path in files_b:
                results['only_in_b'].append((path, md5))
            continue
                
        if not files_b:
            for path in files_a:
                results['only_in_a'].append((path, md5))
            continue
        
        # 找到相同相对路径的文件进行比较
        path_map_a = {path: md5 for path in files_a}
        path_map_b = {path: md5 for path in files_b}
        
        # 检查相同路径的文件
        common_paths = set(path_map_a.keys()) & set(path_map_b.keys())
        for path in common_paths:
            if path_map_a[path] != path_map_b[path]:
                results['content_diff'].append(
                    (path, path_map_a[path], path_map_b[path])
                )
    
    return results

def format_results(results, folder_a, folder_b):
    """格式化输出比较结果"""
    total_diff = (
        len(results['only_in_a']) + 
        len(results['only_in_b']) + 
        len(results['content_diff'])
    )
    
    if total_diff == 0:
        return "yes"
    
    output = []
    output.append(f"🔍 文件夹差异报告:")
    output.append(f"左侧目录: {folder_a}")
    output.append(f"右侧目录: {folder_b}")
    
    if results['only_in_a']:
        output.append("\n🚫 仅存在于左侧的文件:")
        for path, md5 in results['only_in_a']:
            output.append(f"  - {path} (MD5: {md5})")
    
    if results['only_in_b']:
        output.append("\n➕ 仅存在于右侧的文件:")
        for path, md5 in results['only_in_b']:
            output.append(f"  - {path} (MD5: {md5})")
    
    if results['content_diff']:
        output.append("\n🔄 内容不同的文件:")
        for path, md5_a, md5_b in results['content_diff']:
            output.append(f"  - {path}")
            output.append(f"    左侧 MD5: {md5_a}")
            output.append(f"    右侧 MD5: {md5_b}")
    
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(description='比较两个文件夹的文件内容差异（基于MD5）')
    parser.add_argument('folder_a', help='第一个文件夹路径')
    parser.add_argument('folder_b', help='第二个文件夹路径')
    args = parser.parse_args()
    
    if not os.path.isdir(args.folder_a) or not os.path.isdir(args.folder_b):
        print("错误: 输入的路径必须是有效的文件夹")
        exit(1)
    
    folder_a = os.path.abspath(args.folder_a)
    folder_b = os.path.abspath(args.folder_b)
    
    results = compare_folders(folder_a, folder_b)
    output = format_results(results, folder_a, folder_b)
    print(output)

if __name__ == "__main__":
    main()