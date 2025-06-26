import tkinter as tk
from tkinter import ttk, messagebox
from database_operation import Database
from product_edit_window import ProductEditWindow
from utils import SearchPanel, SortableTreeview


class WarehouseWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Склад")
        self.geometry("750x400")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Переменная для хранения всех продуктов (для фильтрации)
        self.all_products = []

        # Панель поиска
        self.search_panel = SearchPanel(self, self.on_search)
        self.search_panel.pack(fill=tk.X, padx=5, pady=5)

        # Таблица товаров
        self.tree = SortableTreeview(self, columns=('id', 'code', 'name', 'buy_price', 'sale_price', 'amount'), show='headings')
        self.tree.heading('id', text='Идентификатор')
        self.tree.heading('code', text='Код товара')
        self.tree.heading('name', text='Наименование')
        self.tree.heading('buy_price', text='Цена закупки')
        self.tree.heading('sale_price', text='Цена продажи')
        self.tree.heading('amount', text='Количество')
        self.tree.column('id', width=30)
        self.tree.column('name', width=150)
        self.tree.column('code', width=100)
        self.tree.column('buy_price', width=80)
        self.tree.column('sale_price', width=80)
        self.tree.column('amount', width=80)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.setup_sorting()

        # Кнопка добавить товар
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X)

        btn_add = tk.Button(btn_frame, text="Добавить товар", command=self.add_product)
        btn_add.pack(side=tk.LEFT, padx=5, pady=5)

        btn_edit = tk.Button(btn_frame, text="Редактировать товар", command=self.edit_product)
        btn_edit.pack(side=tk.LEFT, padx=5, pady=5)

        btn_refresh = tk.Button(btn_frame, text="Обновить", command=self.refresh_products)
        btn_refresh.pack(side=tk.LEFT, padx=5, pady=5)
        # Кнопка удаления товара
        btn_delete = tk.Button(btn_frame, text="Удалить выбранный товар", command=self.delete_selected_product)
        btn_delete.pack(side=tk.LEFT, padx=5)
        # Чекбоксы фильтров
        self.available_var = tk.BooleanVar(value=False)
        self.not_available_var = tk.BooleanVar(value=False)

        cb_available = tk.Checkbutton(btn_frame, text="В наличии", variable=self.available_var,
                                      command=self.on_filter_change)
        cb_available.pack(side=tk.LEFT, padx=5)

        cb_not_available = tk.Checkbutton(btn_frame, text="Только закончившиеся", variable=self.not_available_var,
                                          command=self.on_filter_change)
        cb_not_available.pack(side=tk.LEFT, padx=5)

        self.refresh_products()

    def refresh_products(self):
        self.all_products = self.db.get_all_products()
        self.update_tree(self.all_products)
        self.search_panel.clear()

    def update_tree(self, products):
        # Очищаем дерево
        for i in self.tree.get_children():
            self.tree.delete(i)
        # Вставляем отфильтрованные данные
        for p in products:
            self.tree.insert('', 'end', values=p)

    def on_search(self, query):
        query = query.lower()
        if not query:
            self.update_tree(self.all_products)
            return

        filtered = [p for p in self.all_products if any(query in str(field).lower() for field in p)]
        self.update_tree(filtered)

    def add_product(self):
        ProductEditWindow(self, self.db, self.refresh_products)

    def edit_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для редактирования.")
            return
        item = self.tree.item(selected[0])['values']
        ProductEditWindow(self, self.db, self.refresh_products, product=item)

    def on_filter_change(self):
        # Если включен чекбокс "В наличии"
        if self.available_var.get():
            # Отключаем "Только закончившиеся", чтобы фильтр был один
            if self.not_available_var.get():
                self.not_available_var.set(False)
            products = self.db.get_available_products()
        elif self.not_available_var.get():
            # Если включен "Только закончившиеся"
            products = self.db.get_not_available_products()
        else:
            # Ни один фильтр не включен — показываем все
            products = self.db.get_all_products()

        self.all_products = products
        self.update_tree(products)
        self.search_panel.clear()

    def delete_selected_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для удаления.")
            return
        item = self.tree.item(selected[0])['values']
        product_id = item[0]  # предполагается, что id в первой колонке

        answer = messagebox.askyesno("Подтверждение", f"Удалить товар '{item[2]}'?")
        if not answer:
            return

        try:
            self.db.delete_product(product_id)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить товар: {e}")
            return

        self.refresh_products()

    def on_close(self):
        self.master.child_windows.remove(self)
        self.destroy()