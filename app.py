import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import os
import re


import sql_operations as db


def check_for_drawings():
    print('check')
    files = os.listdir()
    drawings = []
    for i in files:
        print(re.match(r'.*\.idw', i))
        if re.match(r'.*\.idw', i):
            partnumber = i[:len('КЛГИ.777777.777')]
            drawings.append(partnumber)
    db.incert_drawings(drawings)




class DetailCard:
    def __init__(self, parent, detail_data, main_window):
        self.parent = parent
        self.main_window = main_window
        self.detail_data = detail_data

        self.card = tk.Toplevel(parent)
        self.card.title(f"Карточка детали")
        self.card.geometry("450x350")
        self.card.transient(parent)

        # Откладываем grab_set до полного создания окна
        self.card.after(100, self.finalize_window)

        self.create_card_ui()

    def finalize_window(self):
        """Завершающая настройка окна после создания"""
        try:
            """self.card.grab_set()"""
        except tk.TclError:
            # Если grab не сработал, продолжаем без модальности
            pass

    def create_card_ui(self):
        # Распаковываем данные с проверкой
        try:
            # Пытаемся распаковать 6 значений (старая структура)
            part_number, name, amount, parent_id, is_fastener, is_checked, is_borrowed = self.detail_data
        except ValueError:
            try:
                # Пытаемся распаковать 4 значения (новая структура)
                part_number, name, amount, parent_id = self.detail_data
                is_fastener, is_checked, is_borrowed  = 0, 0, 0  # Значения по умолчанию
            except ValueError:
                # Если структура совсем неизвестная
                messagebox.showerror("Ошибка", "Неизвестный формат данных")
                self.card.destroy()
                return

        main_frame = tk.Frame(self.card, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_text = part_number if part_number else "Без обозначения"
        title_label = tk.Label(main_frame, text=f"Деталь: {title_text}",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # Информация
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)

        # Основные поля
        fields = [
            ("Обозначение:", part_number or "Не указано"),
            ("Наименование:", name or "Не указано"),
            ("Количество:", str(amount) if amount else "0"),
            ("ID родителя:", str(parent_id) if parent_id else "Корневой")
        ]

        for i, (label, value) in enumerate(fields):
            tk.Label(info_frame, text=label, font=("Arial", 10, "bold")).grid(row=i, column=0, sticky="w", pady=2)
            value_label = tk.Label(info_frame, text=value, font=("Arial", 10), wraplength=250)
            value_label.grid(row=i, column=1, sticky="w", pady=2)

        # Флажки статусов
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)

        # Переменные для флажков
        self.fastener_var = tk.BooleanVar(value=bool(is_fastener))
        self.checked_var = tk.BooleanVar(value=bool(is_checked))
        self.is_borrowed = tk.BooleanVar(value=bool(is_borrowed))
        # Создаем флажки
        fastener_check = tk.Checkbutton(status_frame, text="Чертеж выпущен",
                                        variable=self.fastener_var, font=("Arial", 10))
        fastener_check.grid(row=0, column=0, sticky="w", pady=2)

        checked_check = tk.Checkbutton(status_frame, text="Нормоконтроль пройден",
                                       variable=self.checked_var, font=("Arial", 10))
        checked_check.grid(row=1, column=0, sticky="w", pady=2)

        is_borrowed_check = tk.Checkbutton(status_frame, text="Заимствован",
                                       variable=self.is_borrowed, font=("Arial", 10))
        is_borrowed_check.grid(row=2, column=0, sticky="w", pady=2)

        # Разделитель
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=15)

        # Кнопки
        button_frame = tk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, pady=(20, 0))

        tk.Button(button_frame, text="Сохранить", command=self.save_status,
                  bg="#4CAF50", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Открыть в Inventor",
                  command=self.open_in_inventor, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Закрыть", command=self.card.destroy,
                  bg="#f44336", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

    def save_status(self):
        """Сохранение статусов в БД"""
        try:
            part_number = self.detail_data[0] if self.detail_data else "Неизвестно"
            is_fastener = 1 if self.fastener_var.get() else 0
            is_checked = 1 if self.checked_var.get() else 0
            is_borrowed = 1 if self.is_borrowed.get() else 0
            db.update_detail_status(part_number, is_fastener, is_checked, is_borrowed)
            # Здесь будет код обновления БД
            self.main_window.load_data()
            messagebox.showinfo("Сохранение", f"Статусы для {part_number} сохранены!")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def open_in_inventor(self):
        part_number = self.detail_data[0] if self.detail_data else "Неизвестно"
        messagebox.showinfo("Inventor", f"Открываю деталь {part_number} в Inventor...")



class InventorMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventor Components Monitor")
        self.root.geometry("900x700")
        self.sort_states = {}


        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Заголовок
        title_label = tk.Label(self.root, text="Мониторинг деталей Inventor",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Кнопка обновления
        refresh_btn = tk.Button(self.root, text="🔄 Обновить данные", command=self.load_data,
                                font=("Arial", 10), bg="#4CAF50", fg="white")
        refresh_btn.pack(pady=5)

        # Создаем Notebook (вкладки)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка 1: Все детали
        self.all_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.all_tab, text="Все детали")

        # Вкладка 2: Стандартные изделия
        self.standard_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.standard_tab, text="Стандартные изделия")

        # Вкладка 3: Прочие изделия
        self.other_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.other_tab, text="Прочие изделия")

        # Создаем таблицы для каждой вкладки
        self.create_table_tab(self.all_tab, "all")
        self.create_table_tab(self.standard_tab, "standard")
        self.create_table_tab(self.other_tab, "other")

        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Панель статистики
        self.create_stats_dashboard()

    def create_stats_dashboard(self):
        """Создает панель с общей статистикой"""
        stats_frame = tk.Frame(self.root, bg='#f0f0f0', relief=tk.RAISED, bd=1)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        data = db.get_info_for_stats()
        # Статистические переменные
        try:
            self.stats_vars = {
                'total': tk.StringVar(value=f"Всего: {data[0]}"),
                'with_drawings': tk.StringVar(value=f"С чертежами: {data[1]}"),
                'checked': tk.StringVar(value=f"Проверено: {data[2]}"),
                'progress': tk.StringVar(value=f"Прогресс: {data[3]}%")
            }
        except:
            self.stats_vars = {
                'total': tk.StringVar(value=f"Всего: 0"),
                'with_drawings': tk.StringVar(value=f"С чертежами: 0"),
                'checked': tk.StringVar(value=f"Проверено: 0"),
                'progress': tk.StringVar(value=f"Прогресс: 0")
            }

        # Создаем метки статистики
        for i, (key, var) in enumerate(self.stats_vars.items()):
            label = tk.Label(stats_frame, textvariable=var, font=("Arial", 10, "bold"),
                             bg='#f0f0f0', fg='#333333')
            label.pack(side=tk.LEFT, padx=15, pady=5)

            # Добавляем разделитель между метками (кроме последней)
            if i < len(self.stats_vars) - 1:
                separator = tk.Frame(stats_frame, width=1, bg='#cccccc', height=20)
                separator.pack(side=tk.LEFT, padx=5)

    def create_table_tab(self, parent, tab_type):
        """Создание таблицы для вкладки"""
        # Фрейм для таблицы с прокруткой
        table_frame = tk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Создание Treeview
        tree = ttk.Treeview(table_frame, columns=("PartNumber", "Name", "Amount", "ParentID", "Drawing", "Checked", "Is_borrowed"),
                            show="headings", height=15)

        # Настройка колонок
        columns_config = [
            ("PartNumber", "Обозначение", 150),
            ("Name", "Наименование", 250),
            ("Amount", "Кол-во", 80),
            ("ParentID", "ID родителя", 100),
            ("Drawing", "Чертеж", 100),
            ("Checked", "Нормаконтроль", 120),
            ("Is_borrowed", "Заим.", 120)

        ]

        for col, heading, width in columns_config:

            tree.heading(col, text=heading, command=lambda c=col: self.sort_column(c))
            tree.column(col, width=width)
            self.sort_states[col] = True

        # Привязка двойного клика
        tree.bind("<Double-1>", lambda e, t=tree: self.on_item_double_click(e, t))

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Размещение
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Сохраняем ссылку на таблицу
        if tab_type == "all":
            self.tree_all = tree
        elif tab_type == "standard":
            self.tree_standard = tree
        else:
            self.tree_other = tree

    def on_item_double_click(self, event, tree):
        """Обработчик двойного клика по строке"""
        selection = tree.selection()
        if selection:
            item = selection[0]
            values = tree.item(item, "values")
            if values:
                DetailCard(self.root, values, self)

    def load_data(self):
        """Загрузка данных во все таблицы"""
        # Очистка всех таблиц
        try:
            self.load_data_from_json()
        except Exception as e:
            print(f'--------------------{e}')
        for tree in [self.tree_all, self.tree_standard, self.tree_other]:
            for item in tree.get_children():
                tree.delete(item)

        # Загрузка данных для каждой вкладки
        try:

            all_details = db.get_details()
            # Пока используем те же данные для всех вкладок
            standard_details = all_details
            other_details = all_details

            # Заполнение таблиц
            self.fill_table(self.tree_all, all_details)
            self.fill_table(self.tree_standard, standard_details)
            self.fill_table(self.tree_other, other_details)

            # Обновление статуса
            self.status_var.set(
                f"Загружено: Всего {len(all_details)} деталей")

        except Exception as e:
            self.status_var.set(f"Ошибка загрузки: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")

    def fill_table(self, tree, details):
        """Заполнение таблицы данными"""
        for detail in details:
            try:
                # Пытаемся распаковать 6 значений
                part_number, name, amount, parent_id, is_fastener, is_checked, is_borrowed = detail
            except ValueError:
                try:
                    # Пытаемся распаковать 4 значения
                    part_number, name, amount, parent_id = detail
                    is_fastener, is_checked, is_borrowed  = 0, 0, 0  # Значения по умолчанию
                except ValueError:
                    # Пропускаем некорректные данные
                    print(f"Пропущен некорректный элемент: {detail}")
                    continue

            # Форматируем статусы
            fastener_status = "✅ Выпущен" if is_fastener else "❌ Не выпущен"
            checked_status = "✅ Пройден" if is_checked else "❌ Не пройден"
            borrowed_status = "✅ Заимствован" if is_borrowed else "❌ Не заимствован"
            tree.insert("", tk.END, values=(
                part_number, name, amount, parent_id, fastener_status, checked_status, borrowed_status
            ))

    def load_data_from_json(self):
        with open("assembly_components.json", 'r') as file:
            try:
                assembly = json.load(file)
            except Exception as e:
                print(e)

        assembly_dict = {}

        for i in assembly:
            try:
                if 'КЛГИ' in i['partNumber']:
                    if i['partNumber'] in assembly_dict:
                        assembly_dict[i['partNumber']]['amount'] = assembly_dict[i['partNumber']]['amount'] + 1
                    else:
                        assembly_dict[i['partNumber']] = {'Description':i["Description"], 'amount': 1, 'parent' :i["parent"]}
            except:
                ...


        for i in assembly_dict:
            if "КЛГИ" in i:
                try:
                    db.inset_into_details(i, assembly_dict[i]["Description"], assembly_dict[i]['amount'], assembly_dict[i]["parent"])

                except Exception as e:
                    print(e)
        check_for_drawings()

    def sort_column(self, column: str):
        """Сортировка колонки"""
        # Получаем индекс колонки
        col_index = self.tree_all['columns'].index(column)

        # Сортируем данные
        data = [(self.tree_all.set(child, column), child) for child in self.tree_all.get_children('')]

        try:
            # Пытаемся отсортировать как числа
            data.sort(key=lambda x: float(x[0]) if x[0].replace('.', '').isdigit() else x[0], reverse=not self.sort_states[column])
        except ValueError:
            # Сортируем как строки
            data.sort(key=lambda x: x[0], reverse=not self.sort_states[column])

        # Перемещаем элементы в отсортированном порядке
        for index, (_, child) in enumerate(data):
            self.tree_all.move(child, '', index)

        # Меняем направление сортировки для следующего раза
        self.sort_states[column] = not self.sort_states[column]


    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


def main():
    root = tk.Tk()
    app = InventorMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()