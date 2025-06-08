from PIL import Image
from PIL.ExifTags import TAGS
import os
import sys

def get_image_shooting_time(image_path):
    """
    获取照片的拍摄时间（从EXIF元数据中提取）
    
    参数:
        image_path (str): 照片文件路径
        
    返回:
        str: 拍摄时间字符串或错误信息
    """
    try:
        # 打开图像文件
        with Image.open(image_path) as img:
            # 获取EXIF数据
            exif_data = img._getexif()
            
            if exif_data is None:
                return "错误: 照片不包含EXIF数据"
            
            # 查找拍摄时间标签
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                # 检查拍摄时间标签（DateTimeOriginal）
                if tag_name == "DateTimeOriginal":
                    return value
            
            return "错误: 照片EXIF中未找到拍摄时间信息"
    
    except FileNotFoundError:
        return f"错误: 文件不存在 - {image_path}"
    except IOError:
        return f"错误: 无法读取文件 - {image_path}"
    except Exception as e:
        return f"错误: {str(e)}"

def main():
    """主函数：处理用户输入并输出结果"""
    # 获取用户输入或命令行参数
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = input("请输入照片文件路径: ").strip()
    
    # 验证文件路径
    if not os.path.isfile(image_path):
        print(f"\n❌ 错误: 文件不存在或不是文件 - {image_path}")
        return
    
    # 获取拍摄时间
    shooting_time = get_image_shooting_time(image_path)
    
    # 打印结果
    print("\n" + "="*50)
    print(f"📷 照片分析结果: {os.path.basename(image_path)}")
    print("="*50)
    print(f"🕒 拍摄时间: {shooting_time}")
    print("="*50)
    
    # 显示完整EXIF数据（可选）
    if "错误" not in shooting_time:
        print("\nℹ️ 完整EXIF数据:")
        with Image.open(image_path) as img:
            exif_data = img._getexif() or {}
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                print(f"{tag_name}: {value}")

if __name__ == "__main__":
    main()
