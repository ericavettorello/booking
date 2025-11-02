"""
Графический интерфейс для системы бронирования.
Использует tkinter для создания GUI с вкладками.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import date, time, datetime
from typing import Optional, List, Dict, Any

import backend


class BookingApp:
    """Главное окно приложения с вкладками."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Система бронирования столов")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Создаем Notebook для вкладок
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создаем вкладки
        self.users_tab = UsersTab(self.notebook)
        self.tables_tab = TablesTab(self.notebook)
        self.bookings_tab = BookingsTab(self.notebook)
        self.database_tab = DatabaseTab(self.notebook)
        
        # Добавляем вкладки
        self.notebook.add(self.users_tab.frame, text="Пользователи")
        self.notebook.add(self.tables_tab.frame, text="Столы")
        self.notebook.add(self.bookings_tab.frame, text="Бронирования")
        self.notebook.add(self.database_tab.frame, text="База данных")


class UsersTab:
    """Вкладка для управления пользователями."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Левая панель - форма для создания/редактирования
        left_frame = ttk.LabelFrame(self.frame, text="Данные пользователя", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Поля ввода
        ttk.Label(left_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.user_id_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.user_id_var, width=30, state="readonly").grid(row=0, column=1, pady=5)
        
        ttk.Label(left_frame, text="Имя *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.name_var, width=30).grid(row=1, column=1, pady=5)
        
        ttk.Label(left_frame, text="Email *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.email_var, width=30).grid(row=2, column=1, pady=5)
        
        ttk.Label(left_frame, text="Пароль:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.password_var, width=30, show="*").grid(row=3, column=1, pady=5)
        
        ttk.Label(left_frame, text="Телефон:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.phone_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.phone_var, width=30).grid(row=4, column=1, pady=5)
        
        ttk.Label(left_frame, text="Роль:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar(value="client")
        role_combo = ttk.Combobox(left_frame, textvariable=self.role_var, width=27, state="readonly")
        role_combo['values'] = ('client', 'admin', 'manager')
        role_combo.grid(row=5, column=1, pady=5)
        
        ttk.Label(left_frame, text="Активен:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.is_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_frame, variable=self.is_active_var).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Кнопки операций
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        ttk.Button(buttons_frame, text="Создать", command=self.create_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Обновить", command=self.update_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Удалить", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        
        # Поиск
        search_frame = ttk.LabelFrame(left_frame, text="Поиск", padding=10)
        search_frame.grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        ttk.Label(search_frame, text="ID или Email:").pack(anchor=tk.W)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(pady=5)
        search_entry.bind('<Return>', lambda e: self.search_user())
        
        ttk.Button(search_frame, text="Найти", command=self.search_user).pack(pady=5)
        
        # Правая панель - список пользователей
        right_frame = ttk.LabelFrame(self.frame, text="Список пользователей", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Фильтры
        filters_frame = ttk.Frame(right_frame)
        filters_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filters_frame, text="Фильтры:").pack(side=tk.LEFT, padx=5)
        
        self.filter_active_var = tk.BooleanVar()
        ttk.Checkbutton(filters_frame, text="Только активные", variable=self.filter_active_var, 
                       command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        
        self.filter_role_var = tk.StringVar()
        role_filter_combo = ttk.Combobox(filters_frame, textvariable=self.filter_role_var, 
                                        width=15, state="readonly")
        role_filter_combo['values'] = ('', 'client', 'admin', 'manager')
        role_filter_combo.pack(side=tk.LEFT, padx=5)
        role_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())
        
        ttk.Button(filters_frame, text="Обновить список", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        
        # Таблица пользователей
        columns = ('ID', 'Имя', 'Email', 'Телефон', 'Роль', 'Активен')
        self.tree = ttk.Treeview(right_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.column('Имя', width=150)
        self.tree.column('Email', width=200)
        
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<Double-1>', self.on_tree_select)
        
        # Загружаем список при инициализации
        self.refresh_list()
        
    def clear_form(self):
        """Очищает форму."""
        self.user_id_var.set("")
        self.name_var.set("")
        self.email_var.set("")
        self.password_var.set("")
        self.phone_var.set("")
        self.role_var.set("client")
        self.is_active_var.set(True)
        
    def create_user(self):
        """Создает нового пользователя."""
        if not self.name_var.get() or not self.email_var.get():
            messagebox.showerror("Ошибка", "Имя и Email обязательны!")
            return
        
        if not self.password_var.get():
            messagebox.showerror("Ошибка", "Пароль обязателен!")
            return
        
        user_id = backend.create_user(
            name=self.name_var.get(),
            email=self.email_var.get(),
            password=self.password_var.get(),
            phone=self.phone_var.get() or None,
            role=self.role_var.get(),
            is_active=self.is_active_var.get()
        )
        
        if user_id:
            messagebox.showinfo("Успех", f"Пользователь создан с ID: {user_id}")
            self.clear_form()
            self.refresh_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось создать пользователя!")
            
    def update_user(self):
        """Обновляет пользователя."""
        user_id = self.user_id_var.get()
        if not user_id:
            messagebox.showerror("Ошибка", "Выберите пользователя для обновления!")
            return
        
        try:
            user_id_int = int(user_id)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный ID пользователя!")
            return
        
        # Подготавливаем данные для обновления
        update_data = {}
        if self.name_var.get():
            update_data['name'] = self.name_var.get()
        if self.email_var.get():
            update_data['email'] = self.email_var.get()
        if self.password_var.get():
            update_data['password'] = self.password_var.get()
        if self.phone_var.get():
            update_data['phone'] = self.phone_var.get()
        
        update_data['role'] = self.role_var.get()
        update_data['is_active'] = self.is_active_var.get()
        
        if backend.update_user(user_id_int, **update_data):
            messagebox.showinfo("Успех", "Пользователь обновлен!")
            self.clear_form()
            self.refresh_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить пользователя!")
            
    def delete_user(self):
        """Удаляет пользователя."""
        user_id = self.user_id_var.get()
        if not user_id:
            messagebox.showerror("Ошибка", "Выберите пользователя для удаления!")
            return
        
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этого пользователя?"):
            return
        
        try:
            user_id_int = int(user_id)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный ID пользователя!")
            return
        
        # Используем мягкое удаление по умолчанию
        if backend.delete_user(user_id_int, hard_delete=False):
            messagebox.showinfo("Успех", "Пользователь удален (деактивирован)!")
            self.clear_form()
            self.refresh_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить пользователя!")
            
    def search_user(self):
        """Ищет пользователя по ID или email."""
        search_value = self.search_var.get().strip()
        if not search_value:
            return
        
        user = None
        try:
            user_id = int(search_value)
            user = backend.get_user(user_id=user_id)
        except ValueError:
            user = backend.get_user(email=search_value)
        
        if user:
            self.user_id_var.set(str(user.get('id', '')))
            self.name_var.set(user.get('name', ''))
            self.email_var.set(user.get('email', ''))
            self.phone_var.set(user.get('phone', '') or '')
            self.role_var.set(user.get('role', 'client'))
            self.is_active_var.set(user.get('is_active', True))
            self.password_var.set("")  # Пароль не показываем
            messagebox.showinfo("Найдено", f"Пользователь найден: {user.get('name', '')}")
        else:
            messagebox.showinfo("Не найдено", "Пользователь не найден!")
            
    def on_tree_select(self, event):
        """Обработчик двойного клика по элементу списка."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        user_id = item['values'][0]
        self.search_var.set(str(user_id))
        self.search_user()
        
    def refresh_list(self):
        """Обновляет список пользователей."""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получаем пользователей с фильтрами
        active_only = self.filter_active_var.get()
        role = self.filter_role_var.get() if self.filter_role_var.get() else None
        
        users = backend.get_all_users(active_only=active_only, role=role)
        
        for user in users:
            self.tree.insert('', tk.END, values=(
                user.get('id', ''),
                user.get('name', ''),
                user.get('email', ''),
                user.get('phone', '') or '',
                user.get('role', ''),
                'Да' if user.get('is_active') else 'Нет'
            ))


class TablesTab:
    """Вкладка для управления столами."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Левая панель - форма
        left_frame = ttk.LabelFrame(self.frame, text="Данные стола", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.table_id_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.table_id_var, width=30, state="readonly").grid(row=0, column=1, pady=5)
        
        ttk.Label(left_frame, text="Номер стола *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.table_number_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.table_number_var, width=30).grid(row=1, column=1, pady=5)
        
        ttk.Label(left_frame, text="Количество мест *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.seats_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.seats_var, width=30).grid(row=2, column=1, pady=5)
        
        ttk.Label(left_frame, text="Статус:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="available")
        status_combo = ttk.Combobox(left_frame, textvariable=self.status_var, width=27, state="readonly")
        status_combo['values'] = ('available', 'unavailable')
        status_combo.grid(row=3, column=1, pady=5)
        
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(buttons_frame, text="Создать", command=self.create_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Обновить", command=self.update_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Удалить", command=self.delete_table).pack(side=tk.LEFT, padx=5)
        
        # Поиск
        search_frame = ttk.LabelFrame(left_frame, text="Поиск", padding=10)
        search_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        ttk.Label(search_frame, text="ID или Номер:").pack(anchor=tk.W)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(pady=5)
        search_entry.bind('<Return>', lambda e: self.search_table())
        
        ttk.Button(search_frame, text="Найти", command=self.search_table).pack(pady=5)
        
        # Правая панель - список
        right_frame = ttk.LabelFrame(self.frame, text="Список столов", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Фильтры
        filters_frame = ttk.Frame(right_frame)
        filters_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filters_frame, text="Фильтры:").pack(side=tk.LEFT, padx=5)
        
        self.filter_status_var = tk.StringVar()
        status_filter_combo = ttk.Combobox(filters_frame, textvariable=self.filter_status_var, 
                                          width=15, state="readonly")
        status_filter_combo['values'] = ('', 'available', 'unavailable')
        status_filter_combo.pack(side=tk.LEFT, padx=5)
        status_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())
        
        ttk.Label(filters_frame, text="Номер стола:").pack(side=tk.LEFT, padx=5)
        self.filter_table_number_var = tk.StringVar()
        ttk.Entry(filters_frame, textvariable=self.filter_table_number_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filters_frame, text="Кол-во мест:").pack(side=tk.LEFT, padx=5)
        self.filter_seats_var = tk.StringVar()
        ttk.Entry(filters_frame, textvariable=self.filter_seats_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filters_frame, text="Обновить", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        
        # Таблица столов
        columns = ('ID', 'Номер стола', 'Кол-во мест', 'Статус')
        self.tree = ttk.Treeview(right_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<Double-1>', self.on_tree_select)
        
        self.refresh_list()
        
    def clear_form(self):
        """Очищает форму."""
        self.table_id_var.set("")
        self.table_number_var.set("")
        self.seats_var.set("")
        self.status_var.set("available")
        
    def create_table(self):
        """Создает новый стол."""
        if not self.table_number_var.get() or not self.seats_var.get():
            messagebox.showerror("Ошибка", "Номер стола и количество мест обязательны!")
            return
        
        try:
            table_number = int(self.table_number_var.get())
            seats = int(self.seats_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Номер стола и количество мест должны быть числами!")
            return
        
        table_id = backend.create_table(
            table_number=table_number,
            seats=seats,
            status=self.status_var.get()
        )
        
        if table_id:
            messagebox.showinfo("Успех", f"Стол создан с ID: {table_id}")
            self.clear_form()
            self.refresh_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось создать стол!")
            
    def update_table(self):
        """Обновляет стол."""
        table_id = self.table_id_var.get()
        if not table_id:
            messagebox.showerror("Ошибка", "Выберите стол для обновления!")
            return
        
        try:
            table_id_int = int(table_id)
            table_number = int(self.table_number_var.get()) if self.table_number_var.get() else None
            seats = int(self.seats_var.get()) if self.seats_var.get() else None
        except ValueError:
            messagebox.showerror("Ошибка", "Неверные числовые значения!")
            return
        
        if backend.update_table(table_id_int, table_number=table_number, 
                               seats=seats, status=self.status_var.get()):
            messagebox.showinfo("Успех", "Стол обновлен!")
            self.clear_form()
            self.refresh_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить стол!")
            
    def delete_table(self):
        """Удаляет стол."""
        table_id = self.table_id_var.get()
        if not table_id:
            messagebox.showerror("Ошибка", "Выберите стол для удаления!")
            return
        
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот стол?"):
            return
        
        try:
            table_id_int = int(table_id)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный ID стола!")
            return
        
        if backend.delete_table(table_id_int):
            messagebox.showinfo("Успех", "Стол удален!")
            self.clear_form()
            self.refresh_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить стол!")
            
    def search_table(self):
        """Ищет стол по ID или номеру."""
        search_value = self.search_var.get().strip()
        if not search_value:
            return
        
        table = None
        try:
            table_id = int(search_value)
            table = backend.get_table(table_id=table_id)
        except ValueError:
            try:
                table_number = int(search_value)
                table = backend.get_table(table_number=table_number)
            except ValueError:
                messagebox.showerror("Ошибка", "Введите число!")
                return
        
        if table:
            self.table_id_var.set(str(table.get('id', '')))
            self.table_number_var.set(str(table.get('table_number', '')))
            self.seats_var.set(str(table.get('seats', '')))
            self.status_var.set(table.get('status', 'available'))
            messagebox.showinfo("Найдено", f"Стол найден: №{table.get('table_number', '')}")
        else:
            messagebox.showinfo("Не найдено", "Стол не найден!")
            
    def on_tree_select(self, event):
        """Обработчик двойного клика по элементу списка."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        table_id = item['values'][0]
        self.search_var.set(str(table_id))
        self.search_table()
        
    def refresh_list(self):
        """Обновляет список столов."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        status = self.filter_status_var.get() if self.filter_status_var.get() else None
        
        # Фильтр по номеру стола
        filter_table_number = None
        if self.filter_table_number_var.get():
            try:
                filter_table_number = int(self.filter_table_number_var.get())
            except ValueError:
                pass
        
        # Фильтр по количеству мест
        filter_seats = None
        if self.filter_seats_var.get():
            try:
                filter_seats = int(self.filter_seats_var.get())
            except ValueError:
                pass
        
        # Получаем все столы и фильтруем вручную
        tables = backend.get_all_tables(status=status)
        
        # Применяем дополнительные фильтры
        filtered_tables = []
        for table in tables:
            # Фильтр по номеру стола
            if filter_table_number is not None:
                if table.get('table_number') != filter_table_number:
                    continue
            
            # Фильтр по количеству мест
            if filter_seats is not None:
                if table.get('seats') != filter_seats:
                    continue
            
            filtered_tables.append(table)
        
        tables = filtered_tables
        
        for table in tables:
            self.tree.insert('', tk.END, values=(
                table.get('id', ''),
                table.get('table_number', ''),
                table.get('seats', ''),
                table.get('status', '')
            ))


class BookingsTab:
    """Вкладка для управления бронированиями."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Левая панель - форма
        left_frame = ttk.LabelFrame(self.frame, text="Данные бронирования", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.booking_id_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.booking_id_var, width=30, state="readonly").grid(row=0, column=1, pady=5)
        
        ttk.Label(left_frame, text="Имя пользователя *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.user_name_var = tk.StringVar()
        # Создаем Combobox для выбора пользователя (можно вводить текст)
        self.user_combo = ttk.Combobox(left_frame, textvariable=self.user_name_var, width=27)
        self.user_combo.grid(row=1, column=1, pady=5)
        self.refresh_user_list()
        
        ttk.Label(left_frame, text="Номер стола *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.table_number_var = tk.StringVar()
        # Создаем Combobox для выбора стола (можно вводить текст)
        self.table_combo = ttk.Combobox(left_frame, textvariable=self.table_number_var, width=27)
        self.table_combo.grid(row=2, column=1, pady=5)
        self.refresh_table_list()
        
        # Скрытые переменные для хранения ID
        self.user_id_var = tk.StringVar()
        self.table_id_var = tk.StringVar()
        
        ttk.Label(left_frame, text="Дата (YYYY-MM-DD) *:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.booking_date_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.booking_date_var, width=30).grid(row=3, column=1, pady=5)
        
        ttk.Label(left_frame, text="Время (HH:MM) *:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.booking_time_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.booking_time_var, width=30).grid(row=4, column=1, pady=5)
        
        # Статус скрыт при создании, всегда будет "reserved"
        self.status_var = tk.StringVar(value="reserved")
        
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(buttons_frame, text="Создать", command=self.create_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Обновить", command=self.update_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Удалить", command=self.delete_booking).pack(side=tk.LEFT, padx=5)
        
        # Проверка доступности
        check_frame = ttk.LabelFrame(left_frame, text="Проверка доступности", padding=10)
        check_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        ttk.Button(check_frame, text="Проверить доступность стола", 
                  command=self.check_availability).pack(pady=5)
        
        self.availability_label = ttk.Label(check_frame, text="", foreground="green")
        self.availability_label.pack()
        
        # Поиск
        search_frame = ttk.LabelFrame(left_frame, text="Поиск", padding=10)
        search_frame.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        ttk.Label(search_frame, text="ID бронирования:").pack(anchor=tk.W)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(pady=5)
        search_entry.bind('<Return>', lambda e: self.search_booking())
        
        ttk.Button(search_frame, text="Найти", command=self.search_booking).pack(pady=5)
        
        # Правая панель - список
        right_frame = ttk.LabelFrame(self.frame, text="Список бронирований", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Фильтры
        filters_frame = ttk.Frame(right_frame)
        filters_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filters_frame, text="Фильтры:").pack(side=tk.LEFT, padx=5)
        
        self.filter_status_var = tk.StringVar()
        status_filter_combo = ttk.Combobox(filters_frame, textvariable=self.filter_status_var, 
                                          width=15, state="readonly")
        status_filter_combo['values'] = ('', 'reserved', 'cancelled', 'pending')
        status_filter_combo.pack(side=tk.LEFT, padx=5)
        status_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())
        
        ttk.Label(filters_frame, text="ID пользователя:").pack(side=tk.LEFT, padx=5)
        self.filter_user_var = tk.StringVar()
        ttk.Entry(filters_frame, textvariable=self.filter_user_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filters_frame, text="ID стола:").pack(side=tk.LEFT, padx=5)
        self.filter_table_var = tk.StringVar()
        ttk.Entry(filters_frame, textvariable=self.filter_table_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filters_frame, text="Обновить", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        
        # Таблица бронирований
        columns = ('ID', 'Пользователь', 'Стол', 'Дата', 'Время', 'Статус')
        self.tree = ttk.Treeview(right_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<Double-1>', self.on_tree_select)
        # Обрабатываем одинарный клик для автоматической загрузки
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        self.refresh_list()
        
    def refresh_user_list(self):
        """Обновляет список пользователей для выпадающего списка."""
        users = backend.get_all_users(active_only=True)
        user_names = [user.get('name', '') for user in users]
        self.user_combo['values'] = user_names
        
    def refresh_table_list(self):
        """Обновляет список столов для выпадающего списка."""
        tables = backend.get_all_tables()
        table_numbers = [str(table.get('table_number', '')) for table in tables]
        self.table_combo['values'] = table_numbers
        
    def get_user_id_by_name(self, name: str) -> Optional[int]:
        """Получает ID пользователя по имени."""
        if not name:
            return None
        users = backend.get_all_users()
        for user in users:
            if user.get('name', '').strip().lower() == name.strip().lower():
                return user.get('id')
        return None
        
    def get_table_id_by_number(self, table_number: str) -> Optional[int]:
        """Получает ID стола по номеру."""
        if not table_number:
            return None
        try:
            table_num = int(table_number)
            table = backend.get_table(table_number=table_num)
            if table:
                return table.get('id')
        except ValueError:
            pass
        return None
        
    def clear_form(self):
        """Очищает форму."""
        self.booking_id_var.set("")
        self.user_name_var.set("")
        self.table_number_var.set("")
        self.user_id_var.set("")
        self.table_id_var.set("")
        self.booking_date_var.set("")
        self.booking_time_var.set("")
        self.status_var.set("reserved")
        self.availability_label.config(text="")
        
    def create_booking(self):
        """Создает новое бронирование."""
        if not all([self.user_name_var.get(), self.table_number_var.get(), 
                   self.booking_date_var.get(), self.booking_time_var.get()]):
            messagebox.showerror("Ошибка", "Все поля обязательны!")
            return
        
        # Получаем ID пользователя по имени
        user_id = self.get_user_id_by_name(self.user_name_var.get())
        if not user_id:
            messagebox.showerror("Ошибка", f"Пользователь '{self.user_name_var.get()}' не найден!")
            return
        
        # Получаем ID стола по номеру
        table_id = self.get_table_id_by_number(self.table_number_var.get())
        if not table_id:
            messagebox.showerror("Ошибка", f"Стол с номером '{self.table_number_var.get()}' не найден!")
            return
        
        try:
            booking_date = datetime.strptime(self.booking_date_var.get(), "%Y-%m-%d").date()
            
            time_str = self.booking_time_var.get()
            if ':' in time_str:
                time_parts = time_str.split(':')
                booking_time = time(int(time_parts[0]), int(time_parts[1]))
            else:
                messagebox.showerror("Ошибка", "Неверный формат времени (используйте HH:MM)")
                return
        except (ValueError, IndexError) as e:
            messagebox.showerror("Ошибка", f"Неверные данные: {e}")
            return
        
        # Проверяем статус стола перед созданием бронирования
        table = backend.get_table(table_id=table_id)
        if table and table.get('status') == 'unavailable':
            messagebox.showerror("Ошибка", 
                f"Стол №{self.table_number_var.get()} недоступен для бронирования (статус: unavailable)!\n"
                "Выберите другой стол.")
            return
        
        # Проверяем доступность стола по времени перед созданием бронирования
        if not backend.check_table_availability(table_id, booking_date, booking_time):
            messagebox.showerror("Ошибка", 
                f"Стол №{self.table_number_var.get()} недоступен на {self.booking_date_var.get()} в {self.booking_time_var.get()}!\n"
                "На это время уже есть бронирование. Выберите другой стол, дату или время.")
            return
        
        # При создании всегда устанавливаем статус "reserved"
        booking_id = backend.create_booking(
            user_id=user_id,
            table_id=table_id,
            booking_date=booking_date,
            booking_time=booking_time,
            status="reserved"
        )
        
        if booking_id:
            messagebox.showinfo("Успех", f"Бронирование создано с ID: {booking_id}")
            self.clear_form()
            self.refresh_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось создать бронирование!")
            
    def update_booking(self):
        """Обновляет бронирование."""
        booking_id = self.booking_id_var.get()
        if not booking_id:
            messagebox.showerror("Ошибка", "Выберите бронирование для обновления!")
            return
        
        try:
            booking_id_int = int(booking_id)
            
            # Получаем ID пользователя по имени, если указано
            user_id = None
            if self.user_name_var.get():
                user_id = self.get_user_id_by_name(self.user_name_var.get())
                if not user_id:
                    messagebox.showerror("Ошибка", f"Пользователь '{self.user_name_var.get()}' не найден!")
                    return
            
            # Получаем ID стола по номеру, если указано
            table_id = None
            if self.table_number_var.get():
                table_id = self.get_table_id_by_number(self.table_number_var.get())
                if not table_id:
                    messagebox.showerror("Ошибка", f"Стол с номером '{self.table_number_var.get()}' не найден!")
                    return
            
            booking_date = None
            if self.booking_date_var.get():
                booking_date = datetime.strptime(self.booking_date_var.get(), "%Y-%m-%d").date()
            
            booking_time = None
            if self.booking_time_var.get():
                time_str = self.booking_time_var.get()
                if ':' in time_str:
                    time_parts = time_str.split(':')
                    booking_time = time(int(time_parts[0]), int(time_parts[1]))
        except (ValueError, IndexError) as e:
            messagebox.showerror("Ошибка", f"Неверные данные: {e}")
            return
        
        # При обновлении не меняем статус автоматически (остается прежним)
        # Статус можно изменить только напрямую в БД при необходимости
        
        if backend.update_booking(booking_id_int, user_id=user_id, table_id=table_id,
                                booking_date=booking_date, booking_time=booking_time,
                                status=None):
            messagebox.showinfo("Успех", "Бронирование обновлено!")
            self.clear_form()
            self.refresh_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить бронирование!")
            
    def delete_booking(self):
        """Удаляет бронирование."""
        booking_id = self.booking_id_var.get()
        if not booking_id:
            messagebox.showerror("Ошибка", "Выберите бронирование для удаления!")
            return
        
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить это бронирование?"):
            return
        
        try:
            booking_id_int = int(booking_id)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный ID бронирования!")
            return
        
        if backend.delete_booking(booking_id_int):
            messagebox.showinfo("Успех", "Бронирование удалено!")
            self.clear_form()
            self.refresh_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить бронирование!")
            
    def check_availability(self):
        """Проверяет доступность стола."""
        if not all([self.table_number_var.get(), self.booking_date_var.get(), 
                   self.booking_time_var.get()]):
            messagebox.showerror("Ошибка", "Заполните номер стола, дату и время!")
            return
        
        # Получаем ID стола по номеру
        table_id = self.get_table_id_by_number(self.table_number_var.get())
        if not table_id:
            messagebox.showerror("Ошибка", f"Стол с номером '{self.table_number_var.get()}' не найден!")
            return
        
        try:
            booking_date = datetime.strptime(self.booking_date_var.get(), "%Y-%m-%d").date()
            
            time_str = self.booking_time_var.get()
            if ':' in time_str:
                time_parts = time_str.split(':')
                booking_time = time(int(time_parts[0]), int(time_parts[1]))
            else:
                messagebox.showerror("Ошибка", "Неверный формат времени")
                return
        except (ValueError, IndexError) as e:
            messagebox.showerror("Ошибка", f"Неверные данные: {e}")
            return
        
        is_available = backend.check_table_availability(table_id, booking_date, booking_time)
        
        if is_available:
            self.availability_label.config(text="✓ Стол доступен", foreground="green")
        else:
            self.availability_label.config(text="✗ Стол недоступен", foreground="red")
            
    def search_booking(self):
        """Ищет бронирование по ID."""
        search_value = self.search_var.get().strip()
        if not search_value:
            return
        
        try:
            booking_id = int(search_value)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число!")
            return
        
        booking = backend.get_booking(booking_id)
        
        if booking:
            self.booking_id_var.set(str(booking.get('id', '')))
            
            # Получаем имя пользователя по ID
            user_id = booking.get('user_id')
            if user_id:
                user = backend.get_user(user_id=user_id)
                if user:
                    self.user_name_var.set(user.get('name', ''))
                    self.user_id_var.set(str(user_id))
            
            # Получаем номер стола по ID
            table_id = booking.get('table_id')
            if table_id:
                table = backend.get_table(table_id=table_id)
                if table:
                    self.table_number_var.set(str(table.get('table_number', '')))
                    self.table_id_var.set(str(table_id))
            
            booking_date = booking.get('booking_date')
            if isinstance(booking_date, str):
                self.booking_date_var.set(booking_date)
            elif booking_date:
                self.booking_date_var.set(booking_date.strftime("%Y-%m-%d"))
            
            booking_time = booking.get('booking_time')
            if isinstance(booking_time, str):
                if ':' in booking_time:
                    self.booking_time_var.set(booking_time[:5])  # HH:MM
            elif booking_time:
                self.booking_time_var.set(booking_time.strftime("%H:%M"))
            
            # Статус не показываем в форме, но храним для справки
            self.status_var.set(booking.get('status', 'reserved'))
            
            # Показываем сообщение только если поиск был ручным (не из списка)
            # Проверяем, был ли вызов из обработчика клика
            if not hasattr(self, '_silent_search'):
                messagebox.showinfo("Найдено", f"Бронирование найдено: ID {booking.get('id', '')}")
            self._silent_search = False
        else:
            if not hasattr(self, '_silent_search'):
                messagebox.showinfo("Не найдено", "Бронирование не найдено!")
            self._silent_search = False
            
    def on_tree_select(self, event):
        """Обработчик клика по элементу списка."""
        selection = self.tree.selection()
        if not selection:
            return
        
        try:
            item = self.tree.item(selection[0])
            booking_id = item['values'][0]
            if booking_id:
                self.search_var.set(str(booking_id))
                # Устанавливаем флаг для беззвучного поиска
                self._silent_search = True
                self.search_booking()
        except (IndexError, KeyError) as e:
            print(f"Ошибка при выборе бронирования: {e}")
        
    def refresh_list(self):
        """Обновляет список бронирований."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        status = self.filter_status_var.get() if self.filter_status_var.get() else None
        
        bookings = []
        if self.filter_user_var.get():
            try:
                user_id = int(self.filter_user_var.get())
                bookings = backend.get_bookings_by_user(user_id)
            except ValueError:
                pass
        elif self.filter_table_var.get():
            try:
                table_id = int(self.filter_table_var.get())
                bookings = backend.get_bookings_by_table(table_id)
            except ValueError:
                pass
        else:
            bookings = backend.get_all_bookings(status=status)
        
        for booking in bookings:
            booking_date = booking.get('booking_date')
            if isinstance(booking_date, date):
                date_str = booking_date.strftime("%Y-%m-%d")
            else:
                date_str = str(booking_date)
            
            booking_time = booking.get('booking_time')
            if isinstance(booking_time, time):
                time_str = booking_time.strftime("%H:%M")
            elif isinstance(booking_time, str):
                time_str = booking_time[:5] if ':' in booking_time else booking_time
            else:
                time_str = str(booking_time)
            
            # Получаем имя пользователя вместо ID
            user_name = ''
            user_id = booking.get('user_id')
            if user_id:
                user = backend.get_user(user_id=user_id)
                if user:
                    user_name = user.get('name', f'ID:{user_id}')
                else:
                    user_name = f'ID:{user_id}'
            
            # Получаем номер стола вместо ID
            table_number = ''
            table_id = booking.get('table_id')
            if table_id:
                table = backend.get_table(table_id=table_id)
                if table:
                    table_number = str(table.get('table_number', f'ID:{table_id}'))
                else:
                    table_number = f'ID:{table_id}'
            
            self.tree.insert('', tk.END, values=(
                booking.get('id', ''),
                user_name,
                table_number,
                date_str,
                time_str,
                booking.get('status', '')
            ))
        
        # Обновляем списки в выпадающих меню
        self.refresh_user_list()
        self.refresh_table_list()


class DatabaseTab:
    """Вкладка для управления базой данных."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.LabelFrame(self.frame, text="Управление базой данных", padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_label = ttk.Label(main_frame, 
                              text="Эта вкладка позволяет инициализировать базу данных\n"
                                   "и создать необходимые таблицы.",
                              font=('Arial', 10))
        info_label.pack(pady=20)
        
        ttk.Button(main_frame, text="Создать все таблицы", 
                 command=self.create_tables).pack(pady=20)
        
        # Область для вывода сообщений
        output_frame = ttk.LabelFrame(main_frame, text="Вывод операций", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
    def create_tables(self):
        """Создает все таблицы в базе данных."""
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Инициализация базы данных...\n")
        self.output_text.insert(tk.END, "=" * 50 + "\n\n")
        self.frame.update()
        
        try:
            backend.create_tables()
            self.output_text.insert(tk.END, "\n✓ Инициализация завершена успешно!\n")
            messagebox.showinfo("Успех", "Таблицы созданы успешно!")
        except Exception as e:
            error_msg = f"\n✗ Ошибка при создании таблиц: {e}\n"
            self.output_text.insert(tk.END, error_msg)
            messagebox.showerror("Ошибка", f"Не удалось создать таблицы: {e}")


def main():
    """Запускает приложение."""
    root = tk.Tk()
    app = BookingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

