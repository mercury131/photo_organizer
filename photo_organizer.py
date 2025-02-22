import os
import shutil
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import re
from tqdm import tqdm

def get_date_from_filename(filename):
    """Парсим дату из имени файла (первый приоритет)"""
    # Ищем форматы: YYYY-MM-DD, YYYYMMDD, YYYY_MM_DD
    patterns = [
        r'\d{4}-\d{2}-\d{2}',    # 2023-12-31
        r'\d{8}',                 # 20231231
        r'\d{4}_\d{2}_\d{2}'      # 2023_12_31
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group()
            try:
                # Преобразуем разные форматы в дату
                if '-' in date_str:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                elif '_' in date_str:
                    return datetime.strptime(date_str, "%Y_%m_%d")
                else:
                    return datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                continue
    return None

def get_date_from_exif(file_path):
    """Пытаемся получить дату из EXIF-данных (второй приоритет)"""
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    if tag_name == 'DateTimeOriginal':
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None

def get_file_date(file_path):
    """Основная функция получения даты с новым приоритетом"""
    filename = os.path.basename(file_path)
    
    # 1. Пытаемся получить дату из имени файла
    date = get_date_from_filename(filename)
    if date:
        return date
    
    # 2. Пробуем EXIF-данные
    date = get_date_from_exif(file_path)
    if date:
        return date
    
    # 3. Используем дату изменения файла
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except OSError:
        pass
    
    # 4. Если все методы не сработали - текущая дата
    return datetime.now()

def organize_photos(source_file='unique.txt', base_output_dir='sorted_photos'):
    # Читаем файл с путями
    with open(source_file, 'r', encoding='utf-8') as f:
        file_paths = [line.strip() for line in f.readlines()]

    # Создаем лог-файлы
    processed = []
    errors = []
    date_sources = {
        'filename': 0,
        'exif': 0,
        'filemtime': 0,
        'fallback': 0
    }

    # Обрабатываем файлы
    for file_path in tqdm(file_paths, desc="Sorting photos"):
        try:
            if not os.path.exists(file_path):
                errors.append(f"File not found: {file_path}")
                continue

            # Получаем дату и источник
            date = get_file_date(file_path)
            source = 'filename' if date else 'fallback'  # временная заглушка
            
            # Определяем реальный источник
            if get_date_from_filename(os.path.basename(file_path)):
                date_sources['filename'] += 1
                source = 'filename'
            elif get_date_from_exif(file_path):
                date_sources['exif'] += 1
                source = 'exif'
            else:
                date_sources['filemtime'] += 1
                source = 'filemtime'

            # Создаем целевую директорию
            year = date.strftime("%Y")
            month = date.strftime("%m - %B")
            target_dir = os.path.join(base_output_dir, year, month)
            os.makedirs(target_dir, exist_ok=True)
            
            # Формируем новое имя
            filename = os.path.basename(file_path)
            new_path = os.path.join(target_dir, filename)
            
            # Разрешаем конфликты имен
            counter = 1
            while os.path.exists(new_path):
                name, ext = os.path.splitext(filename)
                new_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
                counter += 1
            
            # Перемещаем и логируем
            shutil.move(file_path, new_path)
            processed.append(f"{new_path} | Source: {source}")

        except Exception as e:
            errors.append(f"Error processing {file_path}: {str(e)}")

    # Сохраняем отчет
    with open('sorting_report.txt', 'w', encoding='utf-8') as f:
        f.write("=== Date Sources ===\n")
        for k, v in date_sources.items():
            f.write(f"{k}: {v}\n")
            
        f.write("\n=== Processed Files ===\n")
        f.write('\n'.join(processed))
        
        f.write("\n\n=== Errors ===\n")
        f.write('\n'.join(errors))

    print("\n📊 Statistics:")
    print(f"• Files sorted by filename: {date_sources['filename']}")
    print(f"• Files sorted by EXIF: {date_sources['exif']}")
    print(f"• Files sorted by modification date: {date_sources['filemtime']}")
    print(f"• Files with fallback date: {date_sources['fallback']}")
    print(f"\n✅ Total processed: {len(processed)}, Errors: {len(errors)}")

if __name__ == '__main__':
    organize_photos()