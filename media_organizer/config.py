"""
配置文件
"""
import os

# 支持的图片扩展名
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

# 支持的视频扩展名
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v']

# 分组方式：'year' 按年分组，'month' 按年月分组
GROUP_BY = 'month'

# 日志文件路径
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'organizer.log')

# 文件命名正则规则
NAME_PATTERNS = [
    r'(\d{8})_IMG_(\d{4})',  # YYYYMMDD_IMG_HHMM
    r'MTXX_(\d{8})_(\d{6})',  # MTXX_YYYYMMDD_HHMMSS
    r'pt(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})',  # ptYYYY_MM_DD_HH_MM_SS
    r'beauty_(\d{12})'  # beauty_YYYMMDDHHMMSS
]
