import datetime
import os
import logging
import shutil
import utils

# 支持的图片和视频扩展名
SUPPORTED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
    'video': ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv']
}

class FileOrganizer:
    def __init__(self, source_folder, target_folder):
        self.source_folder = source_folder
        self.target_folder = target_folder
        
        # 确保目标目录存在
        os.makedirs(target_folder, exist_ok=True)
        
        self.logger = self.setup_logger()
        
    def setup_logger(self):
        """配置日志系统"""
        logger = logging.getLogger('file_organizer')
        logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        log_file = os.path.join(self.target_folder, 'organizer.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def copy_files(self):
        """复制源文件夹中的所有媒体文件到目标目录"""
        self.logger.info(f"开始从 {self.source_folder} 复制文件到 {self.target_folder}")
        
        # 创建目标目录
        os.makedirs(self.target_folder, exist_ok=True)
        
        # 遍历源文件夹
        for root, _, files in os.walk(self.source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                # 检查文件类型
                if any(ext in exts for exts in SUPPORTED_EXTENSIONS.values()):
                    utils.safe_copy(file_path, self.target_folder)
                    self.logger.info(f"已复制: {file}")
        
        self.logger.info("文件复制完成")
    
    def deduplicate_files(self, folder):
        """基于MD5值去重文件"""
        self.logger.info(f"在 {folder} 中执行去重操作")
        md5_dict = {}
        duplicates = []
        
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            if os.path.isfile(file_path):
                file_md5 = utils.calculate_md5(file_path)
                
                if file_md5 in md5_dict:
                    duplicates.append(file_path)
                else:
                    md5_dict[file_md5] = file_path
        
        # 删除重复文件
        for dup in duplicates:
            os.remove(dup)
            self.logger.info(f"已删除重复文件: {os.path.basename(dup)}")
        
        self.logger.info(f"去重完成，删除了 {len(duplicates)} 个重复文件")
        return len(duplicates)
    
    def classify_files(self):
        """将文件分类到image和video子目录"""
        self.logger.info("开始文件分类")
        
        # 创建分类目录
        image_dir = os.path.join(self.target_folder, 'image')
        video_dir = os.path.join(self.target_folder, 'video')
        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(video_dir, exist_ok=True)
        
        # 移动文件到对应目录
        for file in os.listdir(self.target_folder):
            file_path = os.path.join(self.target_folder, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                
                if ext in SUPPORTED_EXTENSIONS['image']:
                    shutil.move(file_path, os.path.join(image_dir, file))
                elif ext in SUPPORTED_EXTENSIONS['video']:
                    shutil.move(file_path, os.path.join(video_dir, file))
        
        self.logger.info("文件分类完成")
        return image_dir, video_dir
    
    def process_media_folder(self, media_folder, media_type):
        """处理图片或视频文件夹"""
        self.logger.info(f"处理 {media_type} 文件夹: {media_folder}")
        
        # 创建camera和no_camera子目录
        camera_dir = os.path.join(media_folder, 'camera')
        no_camera_dir = os.path.join(media_folder, 'no_camera')
        os.makedirs(camera_dir, exist_ok=True)
        os.makedirs(no_camera_dir, exist_ok=True)
        
        # 第一步：先统一移动文件到对应目录
        for file in os.listdir(media_folder):
            file_path = os.path.join(media_folder, file)
            if os.path.isfile(file_path):
                # 获取创建时间
                creation_time = utils.get_creation_time(file_path)
                
                if creation_time:
                    # 移动到camera目录（保持原名）
                    dest_path = os.path.join(camera_dir, file)
                    shutil.move(file_path, dest_path)
                    self.logger.info(f"已移动至camera目录: {file}")
                else:
                    # 移动到no_camera目录（保持原名）
                    dest_path = os.path.join(no_camera_dir, file)
                    shutil.move(file_path, dest_path)
                    self.logger.info(f"已移动至no_camera目录: {file}")
        
        # 第二步：处理camera目录中的文件（重命名和组织）
        self.process_camera_folder(camera_dir, media_type)
        
        # 第三步：处理no_camera目录中的文件
        self.process_no_camera_folder(no_camera_dir, media_type)
    
    def process_camera_folder(self, camera_dir, media_type):
        """处理camera目录中的文件，按拍摄时间重命名并组织到年份子目录"""
        self.logger.info(f"处理camera目录: {camera_dir}")
        
        for file in os.listdir(camera_dir):
            file_path = os.path.join(camera_dir, file)
            if os.path.isfile(file_path):
                # 获取创建时间
                creation_time = utils.get_creation_time(file_path)
                
                if creation_time:
                    # 格式化时间
                    time_str = utils.format_time(creation_time, "%Y%m%d_%H%M%S")
                    
                    # 创建年份目录
                    year_dir = os.path.join(camera_dir, str(creation_time.year))
                    os.makedirs(year_dir, exist_ok=True)
                    
                    # 重命名文件
                    prefix = "IMG_" if media_type == "image" else "VID_"
                    new_name = f"{prefix}{time_str}{os.path.splitext(file)[1]}"
                    new_path = os.path.join(year_dir, new_name)
                    
                    # 移动并重命名
                    shutil.move(file_path, new_path)
                    self.logger.info(f"已重命名并移动: {file} -> {new_name}")
                else:
                    # 虽然不太可能发生，但安全处理
                    self.logger.warning(f"文件 {file} 在camera目录中但无法获取拍摄时间")
    
    def process_no_camera_folder(self, no_camera_dir, media_type):
        """处理无法获取拍摄时间的文件"""
        self.logger.info(f"处理no_camera文件夹: {no_camera_dir}")
        
        for file in os.listdir(no_camera_dir):
            file_path = os.path.join(no_camera_dir, file)
            if os.path.isfile(file_path):
                # 尝试从文件名提取时间
                # 这里可以扩展更复杂的提取逻辑
                
                # 使用文件修改时间作为后备
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                time_str = utils.format_time(mod_time, "%Y%m%d_%H%M%S")
                
                # 创建年份目录
                year_dir = os.path.join(no_camera_dir, str(mod_time.year))
                os.makedirs(year_dir, exist_ok=True)
                
                # 重命名文件
                prefix = "IMG_" if media_type == "image" else "VID_"
                new_name = f"{prefix}{time_str}{os.path.splitext(file)[1]}"
                new_path = os.path.join(year_dir, new_name)
                
                # 移动并重命名
                shutil.move(file_path, new_path)
                self.logger.info(f"已重命名并移动(使用修改时间): {file} -> {new_name}")
    
    def organize(self):
        """执行完整的整理流程"""
        try:
            # 步骤1: 复制文件
            self.copy_files()
            
            # 步骤2: 第一次去重
            self.deduplicate_files(self.target_folder)
            
            # 步骤3: 分类文件
            image_dir, video_dir = self.classify_files()
            
            # 步骤4: 处理图片和视频
            self.process_media_folder(image_dir, "image")
            self.process_media_folder(video_dir, "video")
            
            # 步骤7: 最终去重
            self.deduplicate_files(self.target_folder)
            
            self.logger.info("文件整理完成!")
            return True
        except Exception as e:
            self.logger.error(f"整理过程中发生错误: {str(e)}", exc_info=True)
            return False
