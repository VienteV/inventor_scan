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
        self.card.geometry("500x550")  # Увеличил для списка сборок
        self.card.transient(parent)

        # Отключаем временно grab_set для корректного отображения
        self.card.after(100, self.finalize_window)

        self.create_card_ui()

    def finalize_window(self):
        try:
            # self.card.grab_set()  # Можно раскомментировать если нужно
            pass
        except tk.TclError:
            pass

    def create_card_ui(self):
        try:
            part_number, name, amount, parent_assemblies_str, is_fastener, is_checked, is_borrowed = self.detail_data

            if parent_assemblies_str and parent_assemblies_str != "—":
                parent_assemblies = [a.strip() for a in parent_assemblies_str.split(',')]
            else:
                parent_assemblies = []
        except:
            pass

        main_frame = tk.Frame(self.card, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_text = part_number if part_number else "Без обозначения"
        title_label = tk.Label(main_frame, text=f"Деталь: {title_text}",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        info_frame = tk.LabelFrame(main_frame, text="Основная информация", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=5)

        fields = [
            ("Обозначение:", part_number or "Не указано"),
            ("Наименование:", name or "Не указано"),
            ("Количество всего:", str(amount) if amount else "0"),
        ]

        for i, (label, value) in enumerate(fields):
            tk.Label(info_frame, text=label, font=("Arial", 10, "bold"),
                     anchor="w").grid(row=i, column=0, sticky="w", pady=3, padx=(0, 10))
            value_label = tk.Label(info_frame, text=value, font=("Arial", 10),
                                   wraplength=300, justify="left", anchor="w")
            value_label.grid(row=i, column=1, sticky="w", pady=3)

        assemblies_frame = tk.LabelFrame(main_frame, text="Входит в сборки:", padx=10, pady=10)
        assemblies_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ("assembly", "quantity")
        self.assemblies_tree = ttk.Treeview(assemblies_frame, columns=columns,
                                            show="headings", height=4)

        self.assemblies_tree.heading("assembly", text="Сборка")
        self.assemblies_tree.heading("quantity", text="Количество в сборке")
        self.assemblies_tree.column("assembly", width=250)
        self.assemblies_tree.column("quantity", width=100, anchor='center')

        scrollbar = ttk.Scrollbar(assemblies_frame, orient=tk.VERTICAL,
                                  command=self.assemblies_tree.yview)
        self.assemblies_tree.configure(yscrollcommand=scrollbar.set)

        self.assemblies_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_assemblies_info(part_number)

        status_frame = tk.LabelFrame(main_frame, text="Статусы", padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=10)

        self.fastener_var = tk.BooleanVar(value=bool(is_fastener))
        self.checked_var = tk.BooleanVar(value=bool(is_checked))
        self.is_borrowed_var = tk.BooleanVar(value=bool(is_borrowed))

        fastener_check = tk.Checkbutton(status_frame, text="Чертеж выпущен",
                                        variable=self.fastener_var,
                                        font=("Arial", 10), anchor="w")
        fastener_check.grid(row=0, column=0, sticky="w", pady=3, padx=5)

        checked_check = tk.Checkbutton(status_frame, text="Нормоконтроль пройден",
                                       variable=self.checked_var,
                                       font=("Arial", 10), anchor="w")
        checked_check.grid(row=1, column=0, sticky="w", pady=3, padx=5)

        is_borrowed_check = tk.Checkbutton(status_frame, text="Заимствованная деталь",
                                           variable=self.is_borrowed_var,
                                           font=("Arial", 10), anchor="w")
        is_borrowed_check.grid(row=2, column=0, sticky="w", pady=3, padx=5)

        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        row1_frame = tk.Frame(buttons_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))

        self.save_btn = tk.Button(row1_frame, text="💾 Сохранить",
                                  command=self.save_status,
                                  bg="#4CAF50", fg="white",
                                  font=("Arial", 10, "bold"),
                                  height=1, width=15)
        self.save_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        manage_btn = tk.Button(row1_frame, text="🔗 Управление связями",
                               command=lambda: self.manage_links(part_number),
                               bg="#9C27B0", fg="white",
                               font=("Arial", 10, "bold"),
                               height=1, width=15)
        manage_btn.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

        # Второй ряд кнопок
        row2_frame = tk.Frame(buttons_frame)
        row2_frame.pack(fill=tk.X)

        # Удалить
        delete_btn = tk.Button(row2_frame, text="🗑️ Удалить деталь",
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

        # Центрируем окно
        self.center_window()

    def load_assemblies_info(self, part_number):
        try:
            # Очищаем дерево
            for item in self.assemblies_tree.get_children():
                self.assemblies_tree.delete(item)

            assemblies = db.get_parent_assemblies_for_part(part_number)

            if not assemblies:
                self.assemblies_tree.insert("", tk.END, values=("— Не входит ни в одну сборку —", ""))
                return

            for assembly in assemblies:
                assembly_part, assembly_name, quantity = assembly
                display_name = f"{assembly_part} - {assembly_name}"
                self.assemblies_tree.insert("", tk.END, values=(display_name, quantity))

        except Exception as e:
            print(f"Ошибка при загрузке информации о сборках: {e}")
            self.assemblies_tree.insert("", tk.END, values=("Ошибка загрузки данных", ""))

    def manage_links(self, part_number):
        try:
            current_links = db.get_parent_assemblies_for_part(part_number)
            current_assemblies = [link[0] for link in current_links]  # Только номера сборок

            all_assemblies = db.get_all_assemblies()

            dialog = tk.Toplevel(self.card)
            dialog.title(f"Управление связями: {part_number}")
            dialog.geometry("500x400")
            dialog.transient(self.card)
            dialog.grab_set()

            dialog.update_idletasks()
            x = self.card.winfo_x() + (self.card.winfo_width() - dialog.winfo_width()) // 2
            y = self.card.winfo_y() + (self.card.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")

            list_frame = tk.LabelFrame(dialog, text="Выберите сборки:", padx=10, pady=10)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            self.assembly_vars = {}

            canvas = tk.Canvas(list_frame)
            scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            for assembly in all_assemblies:
                assembly_id, assembly_part, assembly_name, _ = assembly
                var = tk.BooleanVar(value=assembly_part in current_assemblies)
                chk = tk.Checkbutton(scrollable_frame,
                                     text=f"{assembly_part} - {assembly_name}",
                                     variable=var, anchor="w")
                chk.pack(fill="x", pady=2)
                self.assembly_vars[assembly_part] = var

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            buttons_frame = tk.Frame(dialog)
            buttons_frame.pack(pady=10)

            def save_links():
                selected_assemblies = []
                for assembly_part, var in self.assembly_vars.items():
                    if var.get():
                        selected_assemblies.append(assembly_part)

                try:
                    db.update_part_links(part_number, selected_assemblies)
                    messagebox.showinfo("Успех", "Связи обновлены")
                    self.load_assemblies_info(part_number)  # Обновляем список в карточке
                    self.main_window.load_data()  # Обновляем главное окно
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось обновить связи: {e}")

            tk.Button(buttons_frame, text="Сохранить", command=save_links,
                      bg="#4CAF50", fg="white", width=12).pack(side=tk.LEFT, padx=5)
            tk.Button(buttons_frame, text="Отмена", command=dialog.destroy,
                      bg="#f44336", fg="white", width=12).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть диалог управления связями: {e}")

    def center_window(self):
        self.card.update_idletasks()
        width = self.card.winfo_width()
        height = self.card.winfo_height()
        x = (self.card.winfo_screenwidth() // 2) - (width // 2)
        y = (self.card.winfo_screenheight() // 2) - (height // 2)
        self.card.geometry(f'{width}x{height}+{x}+{y}')

    def save_status(self):
        try:
            part_number = self.detail_data[0] if self.detail_data else "Неизвестно"
            is_fastener = 1 if self.fastener_var.get() else 0
            is_checked = 1 if self.checked_var.get() else 0
            is_borrowed = 1 if self.is_borrowed_var.get() else 0

            db.update_detail_status(part_number, is_fastener, is_checked, is_borrowed)
            self.main_window.load_data()

            # Визуальная обратная связь
            original_text = self.save_btn.cget("text")
            self.save_btn.config(text="✓ Сохранено!", bg="#28a745")
            self.card.after(1500, lambda: self.save_btn.config(text=original_text, bg="#4CAF50"))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def delete_record(self):
        part_number = self.detail_data[0] if self.detail_data else ""
        name = self.detail_data[1] if len(self.detail_data) > 1 else ""

        if not part_number:
            messagebox.showerror("Ошибка", "Не удалось определить деталь для удаления")
            return

        # Получаем информацию о связях перед удалением
        try:
            assemblies = db.get_parent_assemblies_for_part(part_number)
            assemblies_text = ""
            if assemblies:
                assemblies_text = "\n\n⚠️ Деталь входит в сборки:\n"
                for assembly in assemblies[:3]:  # Показываем первые 3
                    assemblies_text += f"  • {assembly[0]} - {assembly[1]}\n"
                if len(assemblies) > 3:
                    assemblies_text += f"  • ... и еще {len(assemblies) - 3} сборок"
        except:
            assemblies = []

        # Подтверждение удаления
        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы действительно хотите удалить деталь?\n\n"
            f"📌 Обозначение: {part_number}\n"
            f"📝 Наименование: {name}"
            f"{assemblies_text}\n\n"
            f"⚠️ Это действие нельзя отменить!\n"
            f"Все данные о детали будут удалены безвозвратно.",
            icon='warning'
        )

        if confirm:
            try:
                # Дополнительное подтверждение если есть связи
                if assemblies:
                    second_confirm = messagebox.askyesno(
                        "Внимание!",
                        f"Деталь связана с {len(assemblies)} сборками.\n"
                        f"Все связи будут удалены.\n"
                        f"Вы уверены, что хотите продолжить?",
                        icon='warning'
                    )
                    if not second_confirm:
                        return

                # Вызываем функцию удаления
                success = db.delete_detail(part_number)

                if success:
                    # Визуальная обратная связь
                    self.save_btn.config(text="✓ Удалено!", bg="#28a745")

                    # Закрываем окно через 1.5 секунды
                    self.card.after(1500, self.card.destroy)

                    # Обновляем главное окно
                    self.main_window.load_data()
                else:
                    messagebox.showerror("Ошибка", f"Не удалось удалить деталь '{part_number}'")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении: {e}")

    def open_in_inventor(self):
        part_number = self.detail_data[0] if self.detail_data else "Неизвестно"
        messagebox.showinfo("Inventor", f"Открываю деталь {part_number} в Inventor...")


class InventorMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventor Components Monitor")
        self.root.geometry("1100x750")
        self.sort_states = {}
        self.current_assembly_filter = "Все сборки"
        self.all_assemblies_cache = []

        self.create_widgets()
        self.load_data()
        self.update_assembly_list()

    def create_widgets(self):
        # Заголовок
        title_label = tk.Label(self.root, text="Мониторинг деталей Inventor",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Панель инструментов
        toolbar_frame = tk.Frame(self.root)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=5)

        # ЛЕВАЯ ГРУППА: фильтр и основные операции
        left_frame = tk.Frame(toolbar_frame)
        left_frame.pack(side=tk.LEFT)

        # Фильтр по сборке
        filter_label = tk.Label(left_frame, text="Фильтр по сборке:", font=("Arial", 10))
        filter_label.pack(side=tk.LEFT, padx=(0, 5))

        self.assembly_filter_var = tk.StringVar(value="Все сборки")
        self.assembly_combo = ttk.Combobox(
            left_frame,
            textvariable=self.assembly_filter_var,
            state="readonly",
            width=35,
            font=("Arial", 10)
        )
        self.assembly_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.assembly_combo.bind("<<ComboboxSelected>>", self.on_assembly_filter_changed)

        # Кнопка сброса фильтра
        reset_filter_btn = tk.Button(
            left_frame,
            text="❌ Сброс",
            command=self.reset_filter,
            font=("Arial", 9),
            bg="#f44336",
            fg="white",
            width=8
        )
        reset_filter_btn.pack(side=tk.LEFT, padx=(0, 15))

        # Кнопки действий
        add_part_btn = tk.Button(
            left_frame,
            text="➕ Деталь",
            command=self.add_part_dialog,
            font=("Arial", 9),
            bg="#2196F3",
            fg="white",
            width=10
        )
        add_part_btn.pack(side=tk.LEFT, padx=(0, 5))

        manage_links_btn = tk.Button(
            left_frame,
            text="🔗 Связи",
            command=self.manage_links_dialog,
            font=("Arial", 9),
            bg="#9C27B0",
            fg="white",
            width=8
        )
        manage_links_btn.pack(side=tk.LEFT, padx=(0, 5))

        # ЦЕНТРАЛЬНАЯ ГРУППА: обновление
        center_frame = tk.Frame(toolbar_frame)
        center_frame.pack(side=tk.LEFT, expand=True)

        refresh_btn = tk.Button(
            center_frame,
            text="🔄 Обновить",
            command=self.load_data,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white",
            width=12
        )
        refresh_btn.pack()

        # ПРАВАЯ ГРУППА: работа с данными
        right_frame = tk.Frame(toolbar_frame)
        right_frame.pack(side=tk.RIGHT)

        # Кнопка загрузки из JSON
        load_json_btn = tk.Button(
            right_frame,
            text="📂 Загрузить JSON",
            command=self.load_from_json,
            font=("Arial", 9),
            bg="#FF9800",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            width=12
        )
        load_json_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Кнопка очистки БД (ВАША ОРИГИНАЛЬНАЯ)
        clear_db_btn = tk.Button(
            right_frame,
            text="🗑️ Очистить БД",
            command=self.clear_database,  # ВЫЗЫВАЕМ ВАШУ ФУНКЦИЮ
            font=("Arial", 9),
            bg="#ff4444",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            width=12
        )
        clear_db_btn.pack(side=tk.LEFT)

        # Панель статистики
        self.create_stats_dashboard()

        # Вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.all_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.all_tab, text="Все детали")

        self.assembly_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.assembly_tab, text="В сборке", state="hidden")

        self.standard_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.standard_tab, text="Стандартные изделия")

        self.create_main_table_tab(self.all_tab, "all")
        self.create_assembly_table_tab(self.assembly_tab, "assembly")
        self.create_main_table_tab(self.standard_tab, "standard")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_from_json(self):
        """Загрузка данных из JSON файла"""
        # Проверяем существование файла
        if not os.path.exists("assembly_components.json"):
            messagebox.showerror(
                "Ошибка",
                "Файл assembly_components.json не найден!\n\n"
                "Убедитесь, что файл находится в той же папке, что и программа."
            )
            return

        # Подтверждение загрузки
        confirm = messagebox.askyesno(
            "Загрузка из JSON",
            "Вы действительно хотите загрузить данные из JSON файла?\n\n"
            "• Существующие детали будут обновлены\n"
            "• Новые детали будут добавлены\n"
            "• Связи между деталями будут перестроены\n\n"
            "Продолжить?",
            icon='question'
        )

        if not confirm:
            return

        try:
            # Обновляем статус
            self.status_var.set("Загрузка данных из JSON...")
            self.root.update()

            # Вызываем вашу существующую функцию
            db.load_from_json()

            # Перезагружаем данные в таблицах
            self.load_data()

            self.status_var.set("Готов")
            messagebox.showinfo("Успех", "Данные успешно загружены из JSON файла!")

        except Exception as e:
            self.status_var.set("Ошибка загрузки")
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные из JSON: {e}")

    # ВАША ОРИГИНАЛЬНАЯ ФУНКЦИЯ ОЧИСТКИ (ПОЛНОСТЬЮ СОХРАНЕНА)
    def clear_database(self):
        """Очистка базы данных с подтверждением"""
        # Первое подтверждение
        confirm1 = messagebox.askyesno(
            "⚠️ ВНИМАНИЕ! Очистка базы данных",
            "Вы действительно хотите ОЧИСТИТЬ всю базу данных?\n\n"
            "Это действие:\n"
            "• Удалит ВСЕ детали\n"
            "• Удалит ВСЕ связи между деталями\n"
            "• Удалит ВСЕ записи о чертежах и проверках\n"
            "• Полностью обнулит статистику\n\n"
            "Данные будут утеряны БЕЗВОЗВРАТНО!",
            icon='warning'
        )

        if not confirm1:
            return

        # Второе подтверждение с вводом текста
        confirm_dialog = tk.Toplevel(self.root)
        confirm_dialog.title("Подтверждение очистки")
        confirm_dialog.geometry("400x200")
        confirm_dialog.transient(self.root)
        confirm_dialog.grab_set()

        # Центрирование
        confirm_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - confirm_dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - confirm_dialog.winfo_height()) // 2
        confirm_dialog.geometry(f"+{x}+{y}")

        # Предупреждение
        warning_label = tk.Label(
            confirm_dialog,
            text="⚠️ ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ ⚠️",
            font=("Arial", 12, "bold"),
            fg="red"
        )
        warning_label.pack(pady=(20, 10))

        info_label = tk.Label(
            confirm_dialog,
            text="Для подтверждения очистки введите 'ОЧИСТИТЬ' в поле ниже:",
            font=("Arial", 10)
        )
        info_label.pack(pady=5)

        # Поле ввода
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(confirm_dialog, textvariable=confirm_var, width=30, font=("Arial", 11))
        confirm_entry.pack(pady=10)
        confirm_entry.focus_set()

        def do_clear():
            if confirm_var.get().strip().upper() == "ОЧИСТИТЬ":
                confirm_dialog.destroy()

                # Третье подтверждение для особо важных случаев
                final_confirm = messagebox.askyesno(
                    "Финальное подтверждение",
                    "Это последний шанс отменить операцию.\n"
                    "Вы абсолютно уверены?",
                    icon='warning'
                )

                if final_confirm:
                    try:
                        # Обновляем статус
                        self.status_var.set("Очистка базы данных...")
                        self.root.update()

                        # Вызываем функцию очистки
                        db.clear_db()

                        # Перезагружаем данные
                        self.load_data()

                        # Показываем сообщение об успехе
                        messagebox.showinfo("Успех", "База данных успешно очищена!")

                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось очистить базу данных: {e}")
                    finally:
                        self.status_var.set("Готов")
            else:
                messagebox.showwarning("Ошибка", "Введен неправильный текст подтверждения")

        # Кнопки
        button_frame = tk.Frame(confirm_dialog)
        button_frame.pack(pady=20)

        clear_btn = tk.Button(
            button_frame,
            text="✅ ОЧИСТИТЬ",
            command=do_clear,
            bg="#ff4444",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(
            button_frame,
            text="❌ Отмена",
            command=confirm_dialog.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Привязка Enter к кнопке очистки
        confirm_entry.bind('<Return>', lambda e: do_clear())

    def create_stats_dashboard(self):
        self.stats_frame = tk.Frame(self.root, bg='#f0f0f0', relief=tk.RAISED, bd=1)
        self.stats_frame.pack(fill=tk.X, padx=10, pady=5)

        # Инициализируем переменные статистики
        self.stats_vars = {
            'total': tk.StringVar(value="Всего: 0"),
            'with_drawings': tk.StringVar(value="С чертежами: 0"),
            'checked': tk.StringVar(value="Проверено: 0"),
            'progress': tk.StringVar(value="Прогресс: 0%"),
            'filter': tk.StringVar(value="Сборка: Все сборки"),
            'assemblies_count': tk.StringVar(value="Сборок: 0")
        }

        stats_labels = []
        for i, (key, var) in enumerate(self.stats_vars.items()):
            label = tk.Label(self.stats_frame, textvariable=var, font=("Arial", 10, "bold"),
                             bg='#f0f0f0', fg='#333333')
            label.pack(side=tk.LEFT, padx=15, pady=5)
            stats_labels.append(label)

            if i < len(self.stats_vars) - 1:
                separator = tk.Frame(self.stats_frame, width=1, bg='#cccccc', height=20)
                separator.pack(side=tk.LEFT, padx=5)

    def create_main_table_tab(self, parent, tab_type):
        table_frame = tk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("PartNumber", "Name", "Amount", "InAssemblies", "Drawing", "Checked", "Is_borrowed")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        columns_config = [
            ("PartNumber", "Обозначение", 150),
            ("Name", "Наименование", 250),
            ("Amount", "Кол-во", 80),
            ("InAssemblies", "В сборках", 150),
            ("Drawing", "Чертеж", 100),
            ("Checked", "Нормаконтроль", 120),
            ("Is_borrowed", "Заим.", 120)
        ]

        for col, heading, width in columns_config:
            tree.heading(col, text=heading, command=lambda c=col: self.sort_column(c, tree))
            tree.column(col, width=width, anchor='center')
            if col != "InAssemblies":
                self.sort_states[(col, tree)] = True

        tree.bind("<Double-1>", lambda e, t=tree: self.on_item_double_click(e, t))

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if tab_type == "all":
            self.tree_all = tree
        elif tab_type == "standard":
            self.tree_standard = tree

    def create_assembly_table_tab(self, parent, tab_type):
        table_frame = tk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("PartNumber", "Name", "QtyInAssembly", "TotalAmount", "Drawing", "Checked", "Is_borrowed")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        columns_config = [
            ("PartNumber", "Обозначение", 150),
            ("Name", "Наименование", 250),
            ("QtyInAssembly", "Кол-во в сборке", 120),
            ("TotalAmount", "Всего на складе", 120),
            ("Drawing", "Чертеж", 100),
            ("Checked", "Нормаконтроль", 120),
            ("Is_borrowed", "Заим.", 120)
        ]

        for col, heading, width in columns_config:
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor='center')

        tree.bind("<Double-1>", lambda e, t=tree: self.on_item_double_click(e, t))

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_assembly = tree

    def on_item_double_click(self, event, tree):
        selection = tree.selection()
        if selection:
            item = selection[0]
            values = tree.item(item, "values")
            if values:
                DetailCard(self.root, values, self)

    def update_assembly_list(self):
        try:
            assemblies_data = db.get_all_assemblies()
            self.all_assemblies_cache = assemblies_data

            assemblies_list = ["Все сборки"]
            assemblies_dict = {}

            for assembly in assemblies_data:
                partNumber = assembly[1]
                name = assembly[2]
                display_name = f"{partNumber} - {name}"
                assemblies_list.append(display_name)
                assemblies_dict[display_name] = assembly[0]  # Сохраняем ID

            self.assembly_combo['values'] = assemblies_list

            self.assemblies_dict = assemblies_dict

        except Exception as e:
            print(f"Ошибка при обновлении списка сборок: {e}")
            self.assembly_combo['values'] = ["Все сборки"]

    def on_assembly_filter_changed(self, event=None):
        selected = self.assembly_filter_var.get()
        self.current_assembly_filter = selected

        if selected == "Все сборки":
            self.notebook.tab(1, state="hidden")
        else:
            self.notebook.tab(1, state="normal")
            self.notebook.tab(1, text=f"В сборке: {selected.split(' - ')[0]}")

        self.load_data()

    def reset_filter(self):
        self.assembly_filter_var.set("Все сборки")
        self.current_assembly_filter = "Все сборки"
        self.notebook.tab(1, state="hidden")
        self.load_data()

    def add_part_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить деталь")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        partNumber_var = tk.StringVar()
        name_var = tk.StringVar()
        amount_var = tk.IntVar(value=1)

        input_frame = tk.Frame(dialog)
        input_frame.pack(pady=20, padx=20, fill=tk.X)

        tk.Label(input_frame, text="Обозначение*:").grid(row=0, column=0, sticky=tk.W, pady=5)
        partNumber_entry = tk.Entry(input_frame, textvariable=partNumber_var, width=30)
        partNumber_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        partNumber_entry.focus_set()

        tk.Label(input_frame, text="Наименование*:").grid(row=1, column=0, sticky=tk.W, pady=5)
        name_entry = tk.Entry(input_frame, textvariable=name_var, width=30)
        name_entry.grid(row=1, column=1, pady=5, padx=(10, 0))

        tk.Label(input_frame, text="Количество:").grid(row=2, column=0, sticky=tk.W, pady=5)
        amount_spinbox = tk.Spinbox(input_frame, from_=1, to=1000, textvariable=amount_var, width=28)
        amount_spinbox.grid(row=2, column=1, pady=5, padx=(10, 0))

        assemblies_frame = tk.LabelFrame(dialog, text="Добавить в сборки:", padx=10, pady=10)
        assemblies_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.assembly_checkboxes = {}
        assemblies_listbox = tk.Frame(assemblies_frame)
        assemblies_listbox.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(assemblies_listbox)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(assemblies_listbox, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=canvas.yview)

        inner_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor=tk.NW)

        for i, assembly in enumerate(self.all_assemblies_cache):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(inner_frame, text=f"{assembly[1]} - {assembly[2]}",
                                 variable=var, anchor=tk.W)
            chk.pack(fill=tk.X, pady=2)
            self.assembly_checkboxes[assembly[0]] = var

        inner_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        buttons_frame = tk.Frame(dialog)
        buttons_frame.pack(pady=10)

        def save_part():
            partNumber = partNumber_var.get().strip()
            name = name_var.get().strip()
            amount = amount_var.get()

            if not partNumber or not name:
                messagebox.showwarning("Внимание", "Заполните обязательные поля (*)")
                return

            selected_assemblies = []
            for assembly_id, var in self.assembly_checkboxes.items():
                if var.get():
                    # Находим номер детали по ID
                    for assembly in self.all_assemblies_cache:
                        if assembly[0] == assembly_id:
                            selected_assemblies.append(assembly[1])
                            break

            try:
                db.insert_into_details(partNumber, name, selected_assemblies)
                messagebox.showinfo("Успех", f"Деталь '{partNumber}' добавлена")
                self.load_data()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить деталь: {e}")

        tk.Button(buttons_frame, text="Сохранить", command=save_part,
                  bg="#4CAF50", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Отмена", command=dialog.destroy,
                  bg="#f44336", fg="white", width=12).pack(side=tk.LEFT, padx=5)

    def manage_links_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Управление связями")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()


        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Выберите деталь:", font=("Arial", 11, "bold")).pack(pady=(15, 5))

        part_combo_frame = tk.Frame(dialog)
        part_combo_frame.pack(pady=5)

        self.selected_part_var = tk.StringVar()
        self.part_combo = ttk.Combobox(part_combo_frame, textvariable=self.selected_part_var,
                                       width=40, state="readonly")
        self.part_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.part_combo.bind("<<ComboboxSelected>>", self.on_part_selected_for_links)

        self.update_part_list_for_links()

        links_frame = tk.LabelFrame(dialog, text="Связи детали со сборками:", padx=10, pady=10)
        links_frame.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)

        columns = ("assembly", "quantity")
        self.links_tree = ttk.Treeview(links_frame, columns=columns, show="headings", height=10)
        self.links_tree.heading("assembly", text="Сборка")
        self.links_tree.heading("quantity", text="Количество")
        self.links_tree.column("assembly", width=350)
        self.links_tree.column("quantity", width=100, anchor='center')

        scrollbar = ttk.Scrollbar(links_frame, orient=tk.VERTICAL, command=self.links_tree.yview)
        self.links_tree.configure(yscrollcommand=scrollbar.set)

        self.links_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="+ Добавить связь",
                  command=self.add_link_dialog, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="✏️ Изменить количество",
                  command=self.edit_quantity_dialog, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="❌ Удалить связь",
                  command=self.remove_link, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)

    def update_part_list_for_links(self):
        try:
            all_parts = db.get_all_parts()
            part_list = [f"{p[0]} - {p[1]}" for p in all_parts]
            self.part_combo['values'] = part_list
            if part_list:
                self.part_combo.set(part_list[0])
                self.on_part_selected_for_links()
        except Exception as e:
            print(f"Ошибка при обновлении списка деталей: {e}")

    def on_part_selected_for_links(self, event=None):
        selected = self.selected_part_var.get()
        if selected:
            part_number = selected.split(' - ')[0]
            self.load_links_for_part(part_number)

    def load_links_for_part(self, part_number):
        for item in self.links_tree.get_children():
            self.links_tree.delete(item)

        try:
            links = db.get_parent_assemblies_for_part(part_number)
            for link in links:
                self.links_tree.insert("", tk.END, values=(f"{link[0]} - {link[1]}", link[2]))
        except Exception as e:
            print(f"Ошибка при загрузке связей: {e}")

    def add_link_dialog(self):
        pass

    def edit_quantity_dialog(self):
        pass

    def remove_link(self):
        selection = self.links_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите связь для удаления")
            return

        item = selection[0]
        values = self.links_tree.item(item, "values")
        assembly_info = values[0].split(' - ')

        if messagebox.askyesno("Подтверждение", f"Удалить связь с сборкой {assembly_info[0]}?"):
            try:
                part_number = self.selected_part_var.get().split(' - ')[0]
                self.load_links_for_part(part_number)
                messagebox.showinfo("Успех", "Связь удалена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить связь: {e}")

    def on_tab_changed(self, event):
        tab_index = self.notebook.index(self.notebook.select())
        if tab_index == 1:  # Вкладка "В сборке"
            self.load_assembly_tab_data()

    def load_assembly_tab_data(self):
        if self.current_assembly_filter == "Все сборки":
            return

        for item in self.tree_assembly.get_children():
            self.tree_assembly.delete(item)

        try:
            assembly_partNumber = self.current_assembly_filter.split(' - ')[0]
            details = db.get_details_by_assembly(assembly_partNumber)

            for detail in details:
                part_number, name, qty_in_assembly, total_amount, drawing, checked, is_borrowed = detail

                drawing_status = "✅ Выпущен" if drawing else "❌ Не выпущен"
                checked_status = "✅ Пройден" if checked else "❌ Не пройден"
                borrowed_status = "✅ Заимствован" if is_borrowed else "❌ Не заимствован"

                self.tree_assembly.insert("", tk.END, values=(
                    part_number, name, qty_in_assembly, total_amount,
                    drawing_status, checked_status, borrowed_status
                ))

        except Exception as e:
            print(f"Ошибка при загрузке данных сборки: {e}")

    def load_data(self):
        self.update_assembly_list()

        for tree in [self.tree_all, self.tree_standard]:
            for item in tree.get_children():
                tree.delete(item)

        try:
            all_details = db.get_details()

            for detail in all_details:
                part_number, name, amount, parent_numbers, drawing, checked, is_borrowed = detail

                drawing_status = "✅ Выпущен" if drawing else "❌ Не выпущен"
                checked_status = "✅ Пройден" if checked else "❌ Не пройден"
                borrowed_status = "✅ Заимствован" if is_borrowed else "❌ Не заимствован"

                if parent_numbers and len(parent_numbers) > 30:
                    parent_display = parent_numbers[:27] + "..."
                else:
                    parent_display = parent_numbers or "—"

                self.tree_all.insert("", tk.END, values=(
                    part_number, name, amount, parent_display,
                    drawing_status, checked_status, borrowed_status
                ))

                if self.is_standard_part(part_number, name):
                    self.tree_standard.insert("", tk.END, values=(
                        part_number, name, amount, parent_display,
                        drawing_status, checked_status, borrowed_status
                    ))

            status_text = f"Загружено: {len(all_details)} деталей"
            if self.current_assembly_filter != "Все сборки":
                status_text += f" (фильтр: {self.current_assembly_filter})"
            self.status_var.set(status_text)

            self.update_stats_dashboard()
            if self.current_assembly_filter != "Все сборки":
                self.load_assembly_tab_data()

        except Exception as e:
            self.status_var.set(f"Ошибка загрузки: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")

    def is_standard_part(self, part_number, name):

        standard_keywords = ["ГОСТ", "ОСТ", "СТП", "ISO", "DIN", "болт", "гайка", "шайба", "штифт"]
        name_lower = name.lower()
        return any(keyword.lower() in name_lower for keyword in standard_keywords)

    def update_stats_dashboard(self):
        try:
            if self.current_assembly_filter == "Все сборки":
                all_details = db.get_details()
                total = len(all_details)
                with_drawings = sum(1 for d in all_details if d[4])  # Индекс 4 = Drawing
                checked = sum(1 for d in all_details if d[5])  # Индекс 5 = Checked
                progress = round((with_drawings + checked) / (2 * total) * 100, 2) if total > 0 else 0
                assemblies_count = len(self.all_assemblies_cache)
            else:
                assembly_partNumber = self.current_assembly_filter.split(' - ')[0]
                data = db.get_info_for_stats_by_assembly(assembly_partNumber)
                total, with_drawings, checked, progress = data
                assemblies_count = 1

            self.stats_vars['total'].set(f"Всего: {total}")
            self.stats_vars['with_drawings'].set(f"С чертежами: {with_drawings}")
            self.stats_vars['checked'].set(f"Проверено: {checked}")
            self.stats_vars['progress'].set(f"Прогресс: {progress}%")
            self.stats_vars['filter'].set(f"Сборка: {self.current_assembly_filter}")
            self.stats_vars['assemblies_count'].set(f"Сборок: {assemblies_count}")

        except Exception as e:
            print(f"Ошибка при обновлении статистики: {e}")
            self.stats_vars['total'].set(f"Всего: 0")
            self.stats_vars['with_drawings'].set(f"С чертежами: 0")
            self.stats_vars['checked'].set(f"Проверено: 0")
            self.stats_vars['progress'].set(f"Прогресс: 0%")
            self.stats_vars['filter'].set(f"Сборка: {self.current_assembly_filter}")
            self.stats_vars['assemblies_count'].set(f"Сборок: 0")

    def sort_column(self, column: str, tree):
        data = [(tree.set(child, column), child) for child in tree.get_children('')]
        sort_state = self.sort_states.get((column, tree), True)

        try:
            data.sort(key=lambda x: float(x[0]) if x[0].replace('.', '').isdigit() else x[0],
                      reverse=not sort_state)
        except ValueError:
            data.sort(key=lambda x: x[0], reverse=not sort_state)


        for index, (_, child) in enumerate(data):
            tree.move(child, '', index)

        self.sort_states[(column, tree)] = not sort_state

    def check_for_drawings(self):
        pass

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


def main():
    root = tk.Tk()
    app = InventorMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()