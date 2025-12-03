import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import os
import re


import sql_operations as db


def check_for_drawings():
    files = os.listdir()
    drawings = []
    for i in files:
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
        self.card.geometry("480x430")  # Увеличил окно для лучшего расположения
        self.card.transient(parent)

        # Откладываем grab_set до полного создания окна
        self.card.after(100, self.finalize_window)

        self.create_card_ui()

    def finalize_window(self):
        """Завершающая настройка окна после создания"""
        try:
            """self.card.grab_set()"""
        except tk.TclError:
            pass

    def create_card_ui(self):
        # Распаковываем данные с проверкой
        try:
            part_number, name, amount, parent_id, is_fastener, is_checked, is_borrowed = self.detail_data
        except ValueError:
            try:
                part_number, name, amount, parent_id = self.detail_data
                is_fastener, is_checked, is_borrowed = 0, 0, 0
            except ValueError:
                messagebox.showerror("Ошибка", "Неизвестный формат данных")
                self.card.destroy()
                return

        main_frame = tk.Frame(self.card, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_text = part_number if part_number else "Без обозначения"
        title_label = tk.Label(main_frame, text=f"Деталь: {title_text}",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # Информация
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)

        fields = [
            ("Обозначение:", part_number or "Не указано"),
            ("Наименование:", name or "Не указано"),
            ("Количество:", str(amount) if amount else "0"),
            ("ID родителя:", str(parent_id) if parent_id else "Корневой")
        ]

        for i, (label, value) in enumerate(fields):
            tk.Label(info_frame, text=label, font=("Arial", 10, "bold"),
                     anchor="w").grid(row=i, column=0, sticky="w", pady=3, padx=(0, 10))
            value_label = tk.Label(info_frame, text=value, font=("Arial", 10),
                                   wraplength=280, justify="left", anchor="w")
            value_label.grid(row=i, column=1, sticky="w", pady=3)

        # Флажки статусов
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=15)

        self.fastener_var = tk.BooleanVar(value=bool(is_fastener))
        self.checked_var = tk.BooleanVar(value=bool(is_checked))
        self.is_borrowed = tk.BooleanVar(value=bool(is_borrowed))

        # Создаем флажки с выравниванием
        fastener_check = tk.Checkbutton(status_frame, text="Чертеж выпущен",
                                        variable=self.fastener_var,
                                        font=("Arial", 10), anchor="w")
        fastener_check.grid(row=0, column=0, sticky="w", pady=3, padx=5)

        checked_check = tk.Checkbutton(status_frame, text="Нормоконтроль пройден",
                                       variable=self.checked_var,
                                       font=("Arial", 10), anchor="w")
        checked_check.grid(row=1, column=0, sticky="w", pady=3, padx=5)

        is_borrowed_check = tk.Checkbutton(status_frame, text="Заимствованная деталь",
                                           variable=self.is_borrowed,
                                           font=("Arial", 10), anchor="w")
        is_borrowed_check.grid(row=2, column=0, sticky="w", pady=3, padx=5)

        # Разделитель
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=15)

        # Кнопки - два ряда по две кнопки
        buttons_container = tk.Frame(main_frame)
        buttons_container.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        # Первый ряд кнопок
        row1_frame = tk.Frame(buttons_container)
        row1_frame.pack(fill=tk.X, pady=(0, 8))

        # Сохранить
        save_btn = tk.Button(row1_frame, text="💾 Сохранить",
                             command=self.save_status,
                             bg="#4CAF50", fg="white",
                             font=("Arial", 10, "bold"),
                             height=1, width=15)
        save_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Открыть в Inventor
        inventor_btn = tk.Button(row1_frame, text="🛠️ Открыть в Inventor",
                                 command=self.open_in_inventor,
                                 bg="#2196F3", fg="white",
                                 font=("Arial", 10, "bold"),
                                 height=1, width=15)
        inventor_btn.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

        # Второй ряд кнопок
        row2_frame = tk.Frame(buttons_container)
        row2_frame.pack(fill=tk.X)

        # Удалить
        delete_btn = tk.Button(row2_frame, text="🗑️ Удалить запись",
                               command=self.delete_record,
                               bg="#dc3545", fg="white",
                               font=("Arial", 10, "bold"),
                               height=1, width=15)
        delete_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Закрыть
        close_btn = tk.Button(row2_frame, text="✕ Закрыть",
                              command=self.card.destroy,
                              bg="#6c757d", fg="white",
                              font=("Arial", 10, "bold"),
                              height=1, width=15)
        close_btn.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

        # Центрируем окно на экране
        self.card.update_idletasks()
        self.center_window()

    def center_window(self):
        """Центрирование окна на экране"""
        self.card.update_idletasks()
        width = self.card.winfo_width()
        height = self.card.winfo_height()
        x = (self.card.winfo_screenwidth() // 2) - (width // 2)
        y = (self.card.winfo_screenheight() // 2) - (height // 2)
        self.card.geometry(f'{width}x{height}+{x}+{y}')

    def save_status(self):
        """Сохранение статусов в БД"""
        try:
            part_number = self.detail_data[0] if self.detail_data else "Неизвестно"
            is_fastener = 1 if self.fastener_var.get() else 0
            is_checked = 1 if self.checked_var.get() else 0
            is_borrowed = 1 if self.is_borrowed.get() else 0

            db.update_detail_status(part_number, is_fastener, is_checked, is_borrowed)
            self.main_window.load_data()

            # Кратковременное подтверждение
            save_btn = self.card.winfo_children()[0].winfo_children()[-2].winfo_children()[0].winfo_children()[0]
            original_text = save_btn.cget("text")
            save_btn.config(text="✓ Сохранено!")
            self.card.after(1500, lambda: save_btn.config(text=original_text))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def delete_record(self):
        """Удаление записи из базы данных"""
        part_number = self.detail_data[0] if self.detail_data else ""
        name = self.detail_data[1] if len(self.detail_data) > 1 else ""

        if not part_number:
            messagebox.showerror("Ошибка", "Не удалось определить запись для удаления")
            return

        # Подтверждение удаления
        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы действительно хотите удалить запись?\n\n"
            f"📌 Обозначение: {part_number}\n"
            f"📝 Наименование: {name}\n\n"
            f"⚠️ Это действие нельзя отменить!\n"
            f"Все данные о детали будут удалены безвозвратно.",
            icon='warning'
        )

        if confirm:
            try:
                # Уточняющее подтверждение для важных записей
                if "КЛГИ" in part_number or amount > 0:
                    second_confirm = messagebox.askyesno(
                        "Еще раз подтвердите",
                        f"Запись '{part_number}' содержит важные данные.\n"
                        f"Вы уверены, что хотите продолжить удаление?",
                        icon='warning'
                    )
                    if not second_confirm:
                        return

                success = db.delete_detail(part_number)

                if success:
                    # Визуальная обратная связь
                    delete_btn = \
                    self.card.winfo_children()[0].winfo_children()[-1].winfo_children()[0].winfo_children()[0]
                    original_text = delete_btn.cget("text")
                    delete_btn.config(text="✓ Удалено!", bg="#28a745")

                    # Закрываем окно через 1.5 секунды
                    self.card.after(1500, self.card.destroy)

                    # Обновляем главное окно
                    self.main_window.load_data()
                else:
                    messagebox.showerror("Ошибка", f"Не удалось удалить запись '{part_number}'")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении: {e}")

    def open_in_inventor(self):
        """Открытие детали в Inventor"""
        part_number = self.detail_data[0] if self.detail_data else "Неизвестно"
        messagebox.showinfo("Inventor", f"Открываю деталь {part_number} в Inventor...")


class InventorMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventor Components Monitor")
        self.root.geometry("900x700")
        self.sort_states = {}
        self.current_assembly_filter = "Все сборки"  # Текущий выбранный фильтр

        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Заголовок
        title_label = tk.Label(self.root, text="Мониторинг деталей Inventor",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Панель инструментов (фильтрация и обновление)
        toolbar_frame = tk.Frame(self.root)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=5)

        # Выпадающий список для выбора родительской сборки
        filter_label = tk.Label(toolbar_frame, text="Фильтр по сборке:", font=("Arial", 10))
        filter_label.pack(side=tk.LEFT, padx=(0, 5))

        self.assembly_filter_var = tk.StringVar(value="Все сборки")
        self.assembly_combo = ttk.Combobox(
            toolbar_frame,
            textvariable=self.assembly_filter_var,
            state="readonly",  # "normal" если хотите ручной ввод
            width=30,
            font=("Arial", 10)
        )
        self.assembly_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.assembly_combo.bind("<<ComboboxSelected>>", self.on_assembly_filter_changed)

        # Кнопка добавления новой сборки
        add_assembly_btn = tk.Button(
            toolbar_frame,
            text="+ Добавить сборку",
            command=self.add_assembly_dialog,
            font=("Arial", 9),
            bg="#2196F3",
            fg="white"
        )
        add_assembly_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Кнопка обновления данных
        refresh_btn = tk.Button(
            toolbar_frame,
            text="🔄 Обновить данные",
            command=self.load_data,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white"
        )
        refresh_btn.pack(side=tk.LEFT)

        # Кнопка сброса фильтра
        reset_filter_btn = tk.Button(
            toolbar_frame,
            text="❌ Сбросить фильтр",
            command=self.reset_filter,
            font=("Arial", 9),
            bg="#f44336",
            fg="white"
        )
        reset_filter_btn.pack(side=tk.LEFT, padx=(10, 0))

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

        # Получаем статистику с учетом фильтра
        if self.current_assembly_filter == "Все сборки":
            data = db.get_info_for_stats()
        else:
            data = db.get_info_for_stats_by_assembly(self.current_assembly_filter)

        # Статистические переменные
        try:
            self.stats_vars = {
                'total': tk.StringVar(value=f"Всего: {data[0]}"),
                'with_drawings': tk.StringVar(value=f"С чертежами: {data[1]}"),
                'checked': tk.StringVar(value=f"Проверено: {data[2]}"),
                'progress': tk.StringVar(value=f"Прогресс: {data[3]}%"),
                'filter': tk.StringVar(value=f"Сборка: {self.current_assembly_filter}")
            }
        except:
            self.stats_vars = {
                'total': tk.StringVar(value=f"Всего: 0"),
                'with_drawings': tk.StringVar(value=f"С чертежами: 0"),
                'checked': tk.StringVar(value=f"Проверено: 0"),
                'progress': tk.StringVar(value=f"Прогресс: 0"),
                'filter': tk.StringVar(value=f"Сборка: {self.current_assembly_filter}")
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
        tree = ttk.Treeview(table_frame,
                            columns=("PartNumber", "Name", "Amount", "ParentID", "Drawing", "Checked", "Is_borrowed"),
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

    def update_assembly_list(self):
        """Обновляет список сборок в выпадающем списке"""
        try:
            # Получаем уникальные родительские сборки из базы данных
            self.assemblies = db.get_unique_assemblies()
            # Добавляем опцию "Все сборки" в начало
            assemblies_list = ["Все сборки"] + list(self.assemblies.keys())
            # Обновляем значения в выпадающем списке
            self.assembly_combo['values'] = assemblies_list
            # Восстанавливаем текущий выбор
            self.assembly_combo.set(self.current_assembly_filter)
        except Exception as e:
            print(f"Ошибка при обновлении списка сборок: {e}")

    def on_assembly_filter_changed(self, event=None):
        """Обработчик изменения выбора сборки"""
        selected = self.assembly_filter_var.get()
        self.current_assembly_filter = selected
        self.load_data()

    def reset_filter(self):
        """Сброс фильтра к значению по умолчанию"""
        self.assembly_filter_var.set("Все сборки")
        self.current_assembly_filter = "Все сборки"
        self.load_data()

    def add_assembly_dialog(self):
        """Диалог добавления новой сборки"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить сборку")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрирование диалога
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # Поле ввода
        tk.Label(dialog, text="Название сборки:", font=("Arial", 10)).pack(pady=(20, 5))
        assembly_entry = tk.Entry(dialog, width=30, font=("Arial", 10))
        assembly_entry.pack(pady=5, padx=20)
        assembly_entry.focus_set()

        # Кнопки
        buttons_frame = tk.Frame(dialog)
        buttons_frame.pack(pady=15)

        def save_assembly():
            assembly_name = assembly_entry.get().strip()
            if assembly_name:
                try:
                    # Здесь можно добавить логику сохранения в базу данных
                    # Например: db.add_assembly_to_list(assembly_name)
                    messagebox.showinfo("Успех", f"Сборка '{assembly_name}' добавлена")
                    self.update_assembly_list()  # Обновляем список
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось добавить сборку: {e}")
            else:
                messagebox.showwarning("Внимание", "Введите название сборки")

        tk.Button(buttons_frame, text="Сохранить", command=save_assembly,
                  bg="#4CAF50", fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Отмена", command=dialog.destroy,
                  bg="#f44336", fg="white", width=10).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """Загрузка данных во все таблицы с учетом фильтра"""
        # Обновляем список сборок
        self.update_assembly_list()

        # Очистка всех таблиц
        try:
            self.load_data_from_json()
        except Exception as e:
            print(f'--------------------{e}')

        for tree in [self.tree_all, self.tree_standard, self.tree_other]:
            for item in tree.get_children():
                tree.delete(item)

        # Загрузка данных для каждой вкладки с учетом фильтра
        try:
            if self.current_assembly_filter == "Все сборки":
                all_details = db.get_details()
            else:
                # Получаем детали только для выбранной сборки
                all_details = db.get_details_by_assembly(self.assemblies[self.current_assembly_filter])

            # Пока используем те же данные для всех вкладок
            standard_details = all_details
            other_details = all_details

            # Заполнение таблиц
            self.fill_table(self.tree_all, all_details)
            self.fill_table(self.tree_standard, standard_details)
            self.fill_table(self.tree_other, other_details)

            # Обновление статуса
            status_text = f"Загружено: {len(all_details)} деталей"
            if self.current_assembly_filter != "Все сборки":
                status_text += f" (фильтр: {self.current_assembly_filter})"
            self.status_var.set(status_text)

            # Обновление статистики
            self.update_stats_dashboard()

        except Exception as e:
            self.status_var.set(f"Ошибка загрузки: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")

    def fill_table(self, tree, details):
        """Заполнение таблицы данными"""
        for detail in details:
            try:
                # Пытаемся распаковать 7 значений
                part_number, name, amount, parent_id, is_fastener, is_checked, is_borrowed = detail
            except ValueError:
                try:
                    # Пытаемся распаковать 4 значения
                    part_number, name, amount, parent_id = detail
                    is_fastener, is_checked, is_borrowed = 0, 0, 0  # Значения по умолчанию
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

    def update_stats_dashboard(self):
        """Обновление панели статистики"""
        # Получаем новые данные статистики
        if self.current_assembly_filter == "Все сборки":
            data = db.get_info_for_stats()
        else:
            data = db.get_info_for_stats_by_assembly(self.assemblies[self.current_assembly_filter])

        # Обновляем переменные
        try:
            self.stats_vars['total'].set(f"Всего: {data[0]}")
            self.stats_vars['with_drawings'].set(f"С чертежами: {data[1]}")
            self.stats_vars['checked'].set(f"Проверено: {data[2]}")
            self.stats_vars['progress'].set(f"Прогресс: {data[3]}%")
            self.stats_vars['filter'].set(f"Сборка: {self.current_assembly_filter}")
        except:
            self.stats_vars['total'].set(f"Всего: 0")
            self.stats_vars['with_drawings'].set(f"С чертежами: 0")
            self.stats_vars['checked'].set(f"Проверено: 0")
            self.stats_vars['progress'].set(f"Прогресс: 0")
            self.stats_vars['filter'].set(f"Сборка: {self.current_assembly_filter}")

    def load_data_from_json(self):
        # Ваш существующий метод
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
                        assembly_dict[i['partNumber']] = {'Description': i["Description"], 'amount': 1,
                                                          'parent': i["parent"]}
            except:
                ...

        for i in assembly_dict:
            if "КЛГИ" in i:
                try:
                    db.inset_into_details(i, assembly_dict[i]["Description"], assembly_dict[i]['amount'],
                                          assembly_dict[i]["parent"])
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
            data.sort(key=lambda x: float(x[0]) if x[0].replace('.', '').isdigit() else x[0],
                      reverse=not self.sort_states[column])
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