import os
import shutil
import tempfile
import pytest
from datetime import datetime
from organize_media import find_and_delete_duplicates, get_media_type, get_creation_date, process_and_group_files

@pytest.fixture
def temp_media_dir():
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)

# 1. 测试删除重复文件
def test_find_and_delete_duplicates(temp_media_dir):
    file1 = os.path.join(temp_media_dir, 'a.jpg')
    file2 = os.path.join(temp_media_dir, 'b.jpg')
    with open(file1, 'wb') as f:
        f.write(b'12345')
    with open(file2, 'wb') as f:
        f.write(b'12345')  # same content
    files = [file1, file2]
    remaining = find_and_delete_duplicates(files, dry_run=False)
    assert len(remaining) == 1
    assert os.path.exists(remaining[0])

# 2. 测试分类照片和视频
@pytest.mark.parametrize("filename,expected", [
    ("test.jpg", "photo"),
    ("test.mp4", "video"),
    ("test.txt", None),
])
def test_get_media_type(filename, expected):
    assert get_media_type(filename) == expected

# 3. 测试文件名提取拍摄时间（含时分秒）
@pytest.mark.parametrize("filename,expected", [
    ("20230101_123456.jpg", datetime(2023,1,1,12,34,56)),
    ("2023-01-01_12.34.56.png", datetime(2023,1,1,12,34,56)),
    ("2023-01-01-12-34-56.mov", datetime(2023,1,1,12,34,56)),
    ("2023-01-01.jpg", datetime(2023,1,1)),
    ("20230101.mp4", datetime(2023,1,1)),
])
def test_get_creation_date_from_filename(tmp_path, filename, expected):
    file_path = tmp_path / filename
    file_path.write_bytes(b'abc')
    dt = get_creation_date(str(file_path))
    assert dt.year == expected.year and dt.month == expected.month and dt.day == expected.day
    if expected.hour != 0 or expected.minute != 0 or expected.second != 0:
        assert dt.hour == expected.hour and dt.minute == expected.minute and dt.second == expected.second

# 4. 测试EXIF/视频元数据提取时间（这里只能模拟EXIF，视频依赖外部库和真实文件）
def test_get_creation_date_from_exif(monkeypatch, tmp_path):
    # 模拟Pillow的Image.open和_exif
    class DummyImg:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def _getexif(self): return {36867: '2022:12:31 23:59:58'}
    monkeypatch.setattr('organize_media.Image', type('Dummy', (), {'open': lambda f: DummyImg()}))
    file_path = tmp_path / "test.jpg"
    file_path.write_bytes(b'abc')
    dt = get_creation_date(str(file_path))
    assert dt == datetime(2022,12,31,23,59,58)

# 5. 测试文件重命名和分组
def test_process_and_group_files(temp_media_dir):
    # 创建一个带时间的文件
    file_path = os.path.join(temp_media_dir, '20230101_123456.jpg')
    with open(file_path, 'wb') as f:
        f.write(b'abc')
    process_and_group_files([file_path], temp_media_dir, dry_run=False)
    target_dir = os.path.join(temp_media_dir, 'photos', '2023-01')
    files = os.listdir(target_dir)
    assert any(f.startswith('20230101_123456') for f in files) 
