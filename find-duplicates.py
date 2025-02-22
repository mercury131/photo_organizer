import os
import sqlite3
from PIL import Image
import imagehash
from multiprocessing import Pool, cpu_count, freeze_support
from tqdm import tqdm
import yaml
import sys
import locale
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

# Фикс для кодировки в Windows
if sys.platform.startswith('win'):
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    locale.setlocale(locale.LC_ALL, 'Russian_Russia.65001')





# Глобальные функции для multiprocessing
def process_file_create(file_path):
    try:
        with Image.open(file_path) as img:
            phash = str(imagehash.phash(img))
            return (phash, file_path)
    except Exception as e:
        return None

def process_file_find(args):
    file_path, db_path = args
    try:
        with Image.open(file_path) as img:
            phash = str(imagehash.phash(img))
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('SELECT file_path FROM images WHERE phash = ?', (phash,))
            result = c.fetchone()
            conn.close()
            return (file_path, result[0] if result else None)
    except Exception as e:
        return (file_path, None)


def create_db(home_library_path, db_path='phash_db.sqlite'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    print("home_library_path - ",home_library_path)
    
    # Создаем таблицу и индексы (если не существуют)
    c.execute('''CREATE TABLE IF NOT EXISTS images 
                (phash TEXT, file_path TEXT UNIQUE)''')  # Добавляем UNIQUE constraint
    c.execute('CREATE INDEX IF NOT EXISTS phash_idx ON images (phash)')
    c.execute('CREATE INDEX IF NOT EXISTS file_path_idx ON images (file_path)')

    # Загружаем существующие пути из БД
    existing_files = set()
    print("🕵️ Checking existing files in database...")
    c.execute('SELECT file_path FROM images')
    for row in c.fetchall():
        existing_files.add(row[0])
    print(f"Found {len(existing_files)} pre-existing files in DB")

    # Фильтруем новые файлы
    print("🔍 Scanning for new files...")
    new_files = []
    for root, _, files in os.walk(home_library_path):
        for f in files:
            file_path = os.path.join(root, f)
            if file_path.lower().endswith(('jpg', 'jpeg', 'png', 'gif', 'bmp')) and file_path not in existing_files:
                new_files.append(file_path)

    total_new = len(new_files)
    if total_new == 0:
        print("✅ All files already in database!")
        conn.close()
        return

    # Обработка только новых файлов с прогресс-баром
    progress = tqdm(total=total_new, desc="Processing", unit="file")
    
    with Pool(cpu_count()) as pool:
        for result in pool.imap_unordered(process_file_create, new_files, chunksize=50):
            if result:
                try:
                    c.execute('INSERT INTO images VALUES (?, ?)', result)
                except sqlite3.IntegrityError:  # На случай параллельных записей
                    pass
            progress.update()
    
    conn.commit()
    progress.close()
    print(f"Added {total_new} new files to database")
    conn.close()


def find_duplicates(new_dirs, db_path='phash_db.sqlite', output_dup='duplicates.txt', output_uniq='unique.txt'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Сбор файлов
    print("🔍 Collecting files to check...")
    new_files = []
    search_roots = [os.path.normpath(d) for d in new_dirs]  # Нормализуем пути для сравнения
    
    for d in new_dirs:
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith(('jpg', 'jpeg', 'png', 'gif', 'bmp')):
                    new_files.append(os.path.join(root, f))

    total_files = len(new_files)
    if total_files == 0:
        print("❌ No files to process!")
        conn.close()
        return

    # Подготовка аргументов
    args_list = [(file_path, db_path) for file_path in new_files]

    # Обработка с прогресс-баром
    duplicates = []
    unique = []
    
    print(f"🕵️ Processing {total_files} files...")
    with tqdm(total=total_files, desc="Analyzing", unit="file") as progress:
        with Pool(cpu_count()) as pool:
            for file_path, original in pool.imap_unordered(process_file_find, args_list):
                if original:
                    duplicates.append((file_path, original))
                else:
                    unique.append(file_path)
                progress.update()

    # Сохранение результатов с корректной кодировкой
    print("💾 Saving results...")
    
    # 1. Полная версия duplicates.txt
    with open(output_dup, 'w', encoding='utf-8', errors='replace') as f:
        f.write('\n'.join([f"{dup[0]}\t{dup[1]}" for dup in duplicates]))
    
    # 2. Фильтрованная версия duplicates_filtered.txt (только из проверяемых директорий)
    filtered_duplicates = [
        dup for dup in duplicates 
        if any(os.path.normpath(dup[0]).startswith(root) for root in search_roots)
    ]
    
    with open('duplicates_filtered.txt', 'w', encoding='utf-8', errors='replace') as f:
        f.write('\n'.join([dup[0] for dup in filtered_duplicates]))
    
    # Файл unique.txt
    with open(output_uniq, 'w', encoding='utf-8', errors='replace') as f:
        f.write('\n'.join(unique))

    conn.close()
    print(f"✅ Done! Duplicates: {len(duplicates)}, Filtered duplicates: {len(filtered_duplicates)}, Unique: {len(unique)}")


def select_directory():
    # Создаем скрытое основное окно Tkinter
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    
    # Открываем диалоговое окно выбора директории
    directory = filedialog.askdirectory(
        title="Выберите каталог для поиска дубликатов",
        initialdir="C:\\",  # Можно задать начальную директорию
        mustexist=True  # Позволяет выбрать только существующие каталоги
    )
    
    if directory:  # Если пользователь выбрал каталог
        normalized_path = Path(directory).resolve().as_posix().replace('/', '\\')
        print("Выбор - ",normalized_path)
        find_duplicates([normalized_path])
    else:
        print("Выбор отменен.")    

if __name__ == '__main__':

    with open('config.yaml', 'r', encoding='utf-8') as file:
        application_config = yaml.safe_load(file)

    photo_db_path=(application_config['library']['path'])

    # Проверка наличия файла
    if not os.path.exists('phash_db.sqlite'):
        create_db(photo_db_path)
        
    else:
        print("Файл phash_db.sqlite существует.")
        select_directory()
    freeze_support()
    # create_db('F:\\Фотографии')  # Раскомментировать для первого запуска
    #find_duplicates(['E:\\Аня фото с дисков\\Google фото Takeout\\Google Фото'])
    