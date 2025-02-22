import os
import sqlite3
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

def find_internal_duplicates(target_dir, db_path='phash_db.sqlite', 
                            output_all='internal_duplicates.txt',
                            output_filtered='internal_duplicates_filtered.txt'):
    # Нормализуем путь для поиска в БД
    target_dir = os.path.normpath(target_dir) + os.sep
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    print("🔍 Searching for files in target directory...")
    # Ищем все файлы в целевой папке и подпапках
    c.execute('''
        SELECT phash, file_path 
        FROM images 
        WHERE file_path LIKE ? || '%'
    ''', (target_dir,))
    
    files_in_target = c.fetchall()
    
    if not files_in_target:
        print("❌ No files found in target directory!")
        conn.close()
        return

    print(f"📁 Found {len(files_in_target)} files in target directory")
    
    # Группируем по phash
    hash_groups = {}
    for phash, file_path in files_in_target:
        if phash not in hash_groups:
            hash_groups[phash] = []
        hash_groups[phash].append(file_path)
    
    # Фильтруем группы с дубликатами
    duplicates = {k: v for k, v in hash_groups.items() if len(v) > 1}
    
    print(f"🔄 Found {len(duplicates)} duplicate groups")
    
    # Формируем списки для записи
    all_duplicates = []
    filtered_duplicates = []
    
    for group in duplicates.values():
        # Записываем все комбинации
        for i in range(len(group)):
            for j in range(i+1, len(group)):
                all_duplicates.append(f"{group[i]}\t{group[j]}")
        
        # Для filtered только первые пути
        filtered_duplicates.extend(group[1:])
    
    # Сохраняем результаты
    print("💾 Saving results...")
    
    # 1. Полный список всех пар дубликатов
    with open(output_all, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_duplicates))
    
    # 2. Список дубликатов для удаления (все копии кроме первого)
    with open(output_filtered, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered_duplicates))
    
    conn.close()
    print(f"✅ Done! Total duplicate pairs: {len(all_duplicates)}, Files to delete: {len(filtered_duplicates)}")
    

def select_directory():
    # Создаем скрытое основное окно Tkinter
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    
    # Открываем диалоговое окно выбора директории
    directory = filedialog.askdirectory(
        title="Выберите каталог для поиска дубликатов (Внутри библиотеки)",
        initialdir="C:\\",  # Можно задать начальную директорию
        mustexist=True  # Позволяет выбрать только существующие каталоги
    )
    
    if directory:  # Если пользователь выбрал каталог
        normalized_path = Path(directory).resolve().as_posix().replace('/', '\\')
        print("Выбор - ",normalized_path)
        find_internal_duplicates(normalized_path)
    else:
        print("Выбор отменен.")  
    

if __name__ == '__main__':
    #target_directory = 'F:\\Фотографии\\2023'  # Укажите нужный путь
    #find_internal_duplicates(target_directory)
    select_directory()