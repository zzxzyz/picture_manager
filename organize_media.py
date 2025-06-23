import os
import argparse
import hashlib
from collections import defaultdict
from datetime import datetime
import re
import logging

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("Pillow is not installed. Please run 'pip install Pillow'")
    Image = None

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
except ImportError:
    print("hachoir is not installed. Please run 'pip install hachoir'")
    createParser = None

PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.heic', '.bmp', '.gif', '.tiff', '.webp', '.raw', '.cr2', '.nef', '.arw'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.3gp', '.mts', '.m2ts', '.webm', '.mpg', '.mpeg', '.rmvb', '.ts'}

# 日志配置
log_time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILENAME = f'organize_media_{log_time_str}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def _calculate_hash(file_path):
    """Calculates the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, OSError) as e:
        logger.error(f"Could not read file {file_path}: {e}")
        return None

def find_and_delete_duplicates(all_files, dry_run=False):
    """Finds and deletes duplicate files based on their content hash."""
    hashes = defaultdict(list)
    for file_path in all_files:
        file_hash = _calculate_hash(file_path)
        if file_hash:
            hashes[file_hash].append(file_path)
    
    duplicates_to_delete = []
    for file_list in hashes.values():
        if len(file_list) > 1:
            # Keep the first file, mark others for deletion
            duplicates_to_delete.extend(file_list[1:])
            
    if not duplicates_to_delete:
        logger.info("No duplicate files found.")
        return all_files # Return original list if no duplicates

    logger.info(f"Found {len(duplicates_to_delete)} duplicate files to remove.")

    remaining_files = []
    for file_path in all_files:
        if file_path not in duplicates_to_delete:
            remaining_files.append(file_path)

    if dry_run:
        for file_path in duplicates_to_delete:
            logger.info(f"DRY-RUN: Would delete duplicate file: {file_path}")
    else:
        for file_path in duplicates_to_delete:
            try:
                os.remove(file_path)
                logger.info(f"Deleted duplicate file: {file_path}")
            except OSError as e:
                logger.error(f"Error deleting file {file_path}: {e}")
    
    return remaining_files

def get_creation_date(file_path):
    """
    Tries to get the creation date of a media file from its metadata.
    Fallback to file system's modification time.
    优先从文件名中提取完整的日期和时间（如YYYY-MM-DD_HH.MM.SS、YYYYMMDD_HHMMSS、YYYY-MM-DD-HH-MM-SS等）。
    """
    filename = os.path.basename(file_path)
    # 优先匹配常见的带时间的格式
    patterns = [
        (r'(\d{4})[-_](\d{2})[-_](\d{2})[-_](\d{2})[.:-](\d{2})[.:-](\d{2})', '%Y-%m-%d-%H.%M.%S'),
        (r'(\d{4})[-_](\d{2})[-_](\d{2})[_-](\d{2})[.:-](\d{2})[.:-](\d{2})', '%Y-%m-%d_%H.%M.%S'),
        (r'(\d{8})[_-](\d{6})', '%Y%m%d_%H%M%S'),
        (r'(\d{4})[-_](\d{2})[-_](\d{2})', '%Y-%m-%d'),
        (r'(\d{8})', '%Y%m%d'),
    ]
    for pattern, fmt in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                if len(match.groups()) >= 6:
                    # 有年月日时分秒
                    dt_str = '_'.join(match.groups())
                    # 统一格式化
                    if fmt == '%Y%m%d_%H%M%S':
                        return datetime.strptime(match.group(1)+match.group(2), '%Y%m%d%H%M%S')
                    else:
                        # 替换所有分隔符为标准格式
                        dt_str = re.sub(r'[-_.:]', '', dt_str)
                        return datetime.strptime(dt_str, '%Y%m%d%H%M%S')
                elif len(match.groups()) == 3:
                    # 只有年月日
                    return datetime.strptime('-'.join(match.groups()), '%Y-%m-%d')
                elif len(match.groups()) == 1 and len(match.group(1)) == 8:
                    return datetime.strptime(match.group(1), '%Y%m%d')
            except Exception:
                pass

    # 2. Try EXIF data for images
    if Image:
        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    # Tag 36867: DateTimeOriginal
                    date_str = exif_data.get(36867)
                    if date_str:
                        return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass # Not an image or no EXIF data

    # 3. Try Hachoir for video metadata
    if createParser:
        try:
            parser = createParser(file_path)
            if parser:
                with parser:
                    metadata = extractMetadata(parser)
                if metadata and metadata.has('creation_date'):
                    return metadata.get('creation_date')
        except Exception:
            pass # Not a video or error parsing

    # 4. Fallback to file modification time
    try:
        return datetime.fromtimestamp(os.path.getmtime(file_path))
    except Exception:
        return None

def get_media_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in PHOTO_EXTS:
        return 'photo'
    elif ext in VIDEO_EXTS:
        return 'video'
    else:
        return None

def process_and_group_files(file_list, source_dir, dry_run=False):
    """
    Renames files based on creation date and groups them into photos/YYYY-MM or videos/YYYY-MM folders.
    """
    logger.info("\nStarting file processing (rename and group)...")
    processed_count = 0
    for file_path in file_list:
        media_type = get_media_type(file_path)
        if not media_type:
            logger.warning(f"Skipping unsupported file type: {file_path}")
            continue

        creation_date = get_creation_date(file_path)
        if not creation_date:
            logger.warning(f"Could not determine creation date for: {file_path}. Skipping.")
            continue

        _, extension = os.path.splitext(file_path)
        new_filename = creation_date.strftime(f"%Y-%m-%d_%H.%M.%S{extension.lower()}")
        
        year_month_folder = creation_date.strftime("%Y-%m")
        if media_type == 'photo':
            target_dir = os.path.join(source_dir, 'photos', year_month_folder)
        else:
            target_dir = os.path.join(source_dir, 'videos', year_month_folder)
        new_file_path = os.path.join(target_dir, new_filename)

        if os.path.abspath(file_path) == os.path.abspath(new_file_path):
            continue

        logger.info(f"Processing: {os.path.basename(file_path)}")
        logger.info(f"  -> New name: {new_file_path}")

        if dry_run:
            processed_count += 1
            continue

        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # To prevent overwriting, check if a file with the new name already exists
            if os.path.exists(new_file_path):
                base, ext = os.path.splitext(new_file_path)
                i = 1
                while os.path.exists(f"{base}_{i}{ext}"):
                    i += 1
                new_file_path = f"{base}_{i}{ext}"
                logger.warning(f"  -> Collision detected. Renaming to: {os.path.basename(new_file_path)}")

            os.rename(file_path, new_file_path)
            processed_count += 1
        except OSError as e:
            logger.error(f"Error moving file {file_path} to {new_file_path}: {e}")

    if processed_count > 0:
        logger.info(f"\nSuccessfully processed and moved {processed_count} files.")
    else:
        logger.info("\nNo files needed processing.")

def organize_media(source_dir, dry_run=False):
    """
    Organizes photos and videos in a directory by deleting duplicates,
    renaming them with shooting date, and grouping them by year and month.
    """
    logger.info(f"Starting media organization for directory: {source_dir}")
    if dry_run:
        logger.info("Running in DRY-RUN mode. No files will be changed.")

    # Step 1: Find all files and remove ignored ones
    all_files = []
    ignored_files = {'.DS_Store'}
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file not in ignored_files:
                all_files.append(os.path.join(root, file))
    
    logger.info(f"Found {len(all_files)} files to process.")

    # Step 2: Delete duplicates
    remaining_files = find_and_delete_duplicates(all_files, dry_run)
    logger.info(f"{len(remaining_files)} files remaining after checking for duplicates.")

    # Step 3: Classify, rename and group files
    process_and_group_files(remaining_files, source_dir, dry_run)

def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(description="Organize photos and videos.")
    parser.add_argument("source_dir", help="The source directory to organize.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes.")
    args = parser.parse_args()

    organize_media(args.source_dir, args.dry_run)

  
if __name__ == "__main__":
    main() 
