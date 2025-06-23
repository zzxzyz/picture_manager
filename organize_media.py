import os
import argparse
import hashlib
from collections import defaultdict
from datetime import datetime
import re

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

def _calculate_hash(file_path):
    """Calculates the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, OSError) as e:
        print(f"Could not read file {file_path}: {e}")
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
        print("No duplicate files found.")
        return all_files # Return original list if no duplicates

    print(f"Found {len(duplicates_to_delete)} duplicate files to remove.")

    remaining_files = []
    for file_path in all_files:
        if file_path not in duplicates_to_delete:
            remaining_files.append(file_path)

    if dry_run:
        for file_path in duplicates_to_delete:
            print(f"DRY-RUN: Would delete duplicate file: {file_path}")
    else:
        for file_path in duplicates_to_delete:
            try:
                os.remove(file_path)
                print(f"Deleted duplicate file: {file_path}")
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")
    
    return remaining_files

def get_creation_date(file_path):
    """
    Tries to get the creation date of a media file from its metadata.
    Fallback to file system's modification time.
    """
    # Regex to find a date in YYYY-MM-DD or YYYY:MM:DD format
    date_pattern = re.compile(r'(\d{4})[:\-](\d{2})[:\-](\d{2})')

    # 1. Check filename first
    filename = os.path.basename(file_path)
    match = date_pattern.search(filename)
    if match:
        try:
            return datetime.strptime(match.group(0).replace(':', '-'), '%Y-%m-%d')
        except ValueError:
            pass # Continue to other methods

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

def process_and_group_files(file_list, source_dir, dry_run=False):
    """
    Renames files based on creation date and groups them into Year/Month folders.
    """
    print("\nStarting file processing (rename and group)...")
    processed_count = 0
    for file_path in file_list:
        creation_date = get_creation_date(file_path)
        if not creation_date:
            print(f"Could not determine creation date for: {file_path}. Skipping.")
            continue

        _, extension = os.path.splitext(file_path)
        new_filename = creation_date.strftime(f"%Y-%m-%d_%H.%M.%S{extension.lower()}")
        
        year_folder = str(creation_date.year)
        month_folder = creation_date.strftime("%m")
        
        target_dir = os.path.join(source_dir, year_folder, month_folder)
        new_file_path = os.path.join(target_dir, new_filename)

        if os.path.abspath(file_path) == os.path.abspath(new_file_path):
            # print(f"File is already correctly named and placed: {file_path}")
            continue

        print(f"Processing: {os.path.basename(file_path)}")
        print(f"  -> New name: {new_file_path}")

        if dry_run:
            processed_count += 1
            continue

        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # To prevent overwriting, check if a file with the new name already exists
            if os.path.exists(new_file_path):
                # Simple collision handling: append a number
                base, ext = os.path.splitext(new_file_path)
                i = 1
                while os.path.exists(f"{base}_{i}{ext}"):
                    i += 1
                new_file_path = f"{base}_{i}{ext}"
                print(f"  -> Collision detected. Renaming to: {os.path.basename(new_file_path)}")

            os.rename(file_path, new_file_path)
            processed_count += 1
        except OSError as e:
            print(f"Error moving file {file_path} to {new_file_path}: {e}")

    if processed_count > 0:
        print(f"\nSuccessfully processed and moved {processed_count} files.")
    else:
        print("\nNo files needed processing.")

def organize_media(source_dir, dry_run=False):
    """
    Organizes photos and videos in a directory by deleting duplicates,
    renaming them with shooting date, and grouping them by year and month.
    """
    print(f"Starting media organization for directory: {source_dir}")
    if dry_run:
        print("Running in DRY-RUN mode. No files will be changed.")

    # Step 1: Find all files and remove ignored ones
    all_files = []
    ignored_files = {'.DS_Store'}
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file not in ignored_files:
                all_files.append(os.path.join(root, file))
    
    print(f"Found {len(all_files)} files to process.")

    # Step 2: Delete duplicates
    remaining_files = find_and_delete_duplicates(all_files, dry_run)
    print(f"{len(remaining_files)} files remaining after checking for duplicates.")

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
