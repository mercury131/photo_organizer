import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

class RestoreViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("File Restore Manager")
        self.master.state('zoomed')
        
        # Инициализация данных
        self.trash_dir = os.path.join(os.getcwd(), 'trash')
        self.log_file = os.path.join(os.getcwd(), 'deletion_log.txt')
        self.deleted_files = self.load_deleted_files()
        self.current_index = 0
        
        # Настройка интерфейса
        self.create_widgets()
        self.show_current_file()

    def load_deleted_files(self):
        """Загрузка списка удаленных файлов из лога"""
        deleted_files = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    parts = line.strip().split(' ', 1)
                    if len(parts) == 2:
                        filename, original_path = parts
                        deleted_files.append({
                            'filename': filename,
                            'original_path': original_path,
                            'trash_path': os.path.join(self.trash_dir, filename)
                        })
        return deleted_files

    def create_widgets(self):
        """Создание элементов интерфейса с исправленным layout"""
        # Главный контейнер
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Панель управления (перемещена выше)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=10)  # Перемещено вверх
        ttk.Button(control_frame, text="<< Назад", command=self.prev_file).pack(side=tk.LEFT, padx=20)
        ttk.Button(control_frame, text="Восстановить", command=self.restore_file).pack(side=tk.LEFT, padx=20)
        ttk.Button(control_frame, text="Вперед >>", command=self.next_file).pack(side=tk.LEFT, padx=20)

        # Контейнер для изображения и списка
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Панель изображения с фиксированной высотой
        self.image_frame = ttk.Frame(content_frame)
        self.image_frame.pack(fill=tk.BOTH, expand=True)

        # Список удаленных файлов
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(fill=tk.X, pady=10)

        self.files_tree = ttk.Treeview(
            list_frame,
            columns=('num', 'filename', 'original_path'),
            show='headings',
            height=8
        )

        self.files_tree.heading('num', text='№', anchor=tk.W)
        self.files_tree.heading('filename', text='Имя файла', anchor=tk.W)
        self.files_tree.heading('original_path', text='Исходный путь', anchor=tk.W)

        self.files_tree.column('num', width=50, stretch=False)
        self.files_tree.column('filename', width=200)
        self.files_tree.column('original_path', width=500)

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscroll=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.files_tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        # Статус бар (под панелью управления)
        self.status = ttk.Label(main_frame, text="", anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # Заполнение списка
        self.populate_files_list()

    def populate_files_list(self):
        """Заполнение списка файлов"""
        for i, file_info in enumerate(self.deleted_files, 1):
            self.files_tree.insert(
                '', 
                tk.END, 
                values=(i, file_info['filename'], file_info['original_path'])
            )

    def on_tree_select(self, event):
        """Обработка выбора в списке"""
        if selected := self.files_tree.selection():
            self.current_index = self.files_tree.index(selected[0])
            self.show_current_file()

    def show_current_file(self):
        """Отображение текущего файла с исправлением масштабирования"""
        for widget in self.image_frame.winfo_children():
            widget.destroy()

        if not self.deleted_files:
            self.status.config(text="Нет файлов для восстановления!")
            return

        file_info = self.deleted_files[self.current_index]
        
        try:
            # Обновляем геометрию перед расчетами
            self.master.update_idletasks()
            
            # Расчет размеров с защитой от нулевых значений
            max_width = max(100, self.master.winfo_width() - 100)
            max_height = max(100, self.master.winfo_height() - 300)
            
            # Загрузка изображения
            img = Image.open(file_info['trash_path'])
            img.thumbnail((max_width, max_height))
            
            self.current_image = ImageTk.PhotoImage(img)
            
            # Контейнер для центрирования
            img_container = ttk.Frame(self.image_frame)
            img_container.pack(expand=True, fill=tk.BOTH)
            
            ttk.Label(img_container, image=self.current_image).pack(expand=True)

            # Отображение информации
            ttk.Label(
                self.image_frame, 
                text=f"Исходный путь: {file_info['original_path']}",
                wraplength=max_width
            ).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {str(e)}")

        self.status.config(text=f"Файл {self.current_index + 1} из {len(self.deleted_files)}")

    def restore_file(self):
        """Восстановление файла"""
        if not self.deleted_files:
            return

        file_info = self.deleted_files[self.current_index]
        
        # Проверка существования файла в корзине
        if not os.path.exists(file_info['trash_path']):
            messagebox.showerror("Ошибка", "Файл не найден в корзине!")
            return

        # Проверка целевого пути
        target_dir = os.path.dirname(file_info['original_path'])
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать директорию: {str(e)}")
                return

        # Проверка существования файла в целевой локации
        if os.path.exists(file_info['original_path']):
            choice = messagebox.askyesno("Подтверждение", 
                                       "Файл уже существует. Перезаписать?")
            if not choice:
                return

        try:
            shutil.move(file_info['trash_path'], file_info['original_path'])
            self.remove_from_log(file_info)
            self.deleted_files.pop(self.current_index)
            self.update_interface()
            messagebox.showinfo("Успех", "Файл успешно восстановлен!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка восстановления: {str(e)}")

    def remove_from_log(self, file_info):
        """Удаление записи из лог-файла"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.strip() != f"{file_info['filename']} {file_info['original_path']}":
                        f.write(line)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка обновления лога: {str(e)}")

    def update_interface(self):
        """Обновление интерфейса после восстановления"""
        self.files_tree.delete(*self.files_tree.get_children())
        self.populate_files_list()
        self.current_index = max(0, self.current_index - 1)
        self.show_current_file()

    def prev_file(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_file()

    def next_file(self):
        if self.current_index < len(self.deleted_files) - 1:
            self.current_index += 1
            self.show_current_file()

if __name__ == '__main__':
    root = tk.Tk()
    app = RestoreViewer(root)
    root.mainloop()