import os
import shutil
from pathlib import Path

def move_duplicates_to_trash(duplicates_file='duplicates_filtered.txt'):
    # Создаем папку Trash в рабочей директории
    trash_dir = os.path.join(os.getcwd(), 'Trash')
    os.makedirs(trash_dir, exist_ok=True)

    # Читаем файл с дубликатами
    if not os.path.exists(duplicates_file):
        print(f"❌ Файл {duplicates_file} не найден!")
        return

    moved_count = 0
    errors = []

    with open(duplicates_file, 'r', encoding='utf-8') as f:
        file_paths = f.read().splitlines()

    print(f"🔍 Найдено {len(file_paths)} файлов для перемещения")

    for orig_path in file_paths:
        try:
            # Чистим путь от возможных кавычек и лишних слешей
            clean_path = orig_path.strip().replace('\\', '/').replace('//', '/')
            clean_path = clean_path.strip('"').replace('/', '\\')
            
            if not os.path.exists(clean_path):
                errors.append(f"Файл не существует: {clean_path}")
                continue

            # Формируем новый путь
            filename = os.path.basename(clean_path)
            dest_path = os.path.join(trash_dir, filename)

            # Обрабатываем коллизии имен
            counter = 1
            while os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                dest_path = os.path.join(trash_dir, f"{name}_{counter}{ext}")
                counter += 1

            # Перемещаем файл
            shutil.move(clean_path, dest_path)
            moved_count += 1
            print(f"✓ Успешно перемещен: {filename}")

        except Exception as e:
            errors.append(f"Ошибка при перемещении {orig_path}: {str(e)}")

    # Выводим отчет
    print("\n📝 Отчет:")
    print(f"• Успешно перемещено: {moved_count}")
    print(f"• Ошибок: {len(errors)}")
    
    if errors:
        print("\n🚨 Список ошибок:")
        for error in errors[:5]:  # Показываем первые 5 ошибок
            print(f"  {error}")
        if len(errors) > 5:
            print(f"  ... и еще {len(errors)-5} ошибок")

if __name__ == '__main__':
    move_duplicates_to_trash()