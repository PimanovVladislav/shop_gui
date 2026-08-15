import tkinter as tk
from tkinter import messagebox
from database_operation import Database
from product_edit_window import ProductEditWindow
from utils import SearchPanel, SortableTreeview, bind_entry_shortcuts
from excel_export import ExcelExporter


class WarehouseWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Склад")
        self.geometry("900x500")
        self.state('zoomed')
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.all_products = []
        self.edit_queue = []

        self.search_panel = SearchPanel(self, self.on_search)
        self.search_panel.pack(fill=tk.X, padx=5, pady=5)

        self.tree = SortableTreeview(
            self,
            columns=('check', 'id', 'code', 'name',
                     'buy_price', 'sale_price', 'amount'),
            show='headings',
            checkbox_column=True
        )
        self.tree.heading('check', text='☐')
        self.tree.heading('id', text='ID')
        self.tree.heading('code', text='Код товара')
        self.tree.heading('name', text='Наименование')
        self.tree.heading('buy_price', text='Цена закупки')
        self.tree.heading('sale_price', text='Цена продажи')
        self.tree.heading('amount', text='Количество')

        self.tree.column('check', width=30, stretch=False)
        self.tree.column('id', width=50)
        self.tree.column('code', width=100)
        self.tree.column('name', width=200)
        self.tree.column('buy_price', width=100)
        self.tree.column('sale_price', width=100)
        self.tree.column('amount', width=90)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.tree.setup_sorting()

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="Добавить товар",
                  command=self.add_product).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Редактировать",
                  command=self.edit_product).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Редактировать выбранные",
                  command=self.edit_selected).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Обновить",
                  command=self.refresh_products).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Удалить выбранное",
                  command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Экспорт в Excel",
                  command=self.export_to_excel).pack(side=tk.LEFT, padx=2)

        self.available_var = tk.BooleanVar(value=False)
        self.not_available_var = tk.BooleanVar(value=False)

        tk.Checkbutton(btn_frame, text="В наличии",
                       variable=self.available_var,
                       command=self.on_filter_change).pack(
            side=tk.LEFT, padx=(20, 5))
        tk.Checkbutton(btn_frame, text="Закончившиеся",
                       variable=self.not_available_var,
                       command=self.on_filter_change).pack(
            side=tk.LEFT, padx=5)

        self.refresh_products()

    def refresh_products(self):
        self.all_products = self.db.get_all_products()
        self.update_tree(self.all_products)
        self.search_panel.clear()

    def update_tree(self, products):
        self.tree.delete(*self.tree.get_children())
        for p in products:
            self.tree.insert('', 'end', iid=str(p[0]), values=p)

    def on_search(self, query):
        query = query.lower()
        if not query:
            self.update_tree(self.all_products)
            return
        search_col = self.tree.get_search_column()
        # индексы кортежа product: (id, code, name, buy_price, sale_price, amount)
        mapping = {'id': 0, 'code': 1, 'name': 2,
                   'buy_price': 3, 'sale_price': 4, 'amount': 5}
        filtered = []
        if search_col is not None and search_col in mapping:
            src_index = mapping[search_col]
            for p in self.all_products:
                if src_index < len(p) and query in str(p[src_index]).lower():
                    filtered.append(p)
        else:
            filtered = [p for p in self.all_products
                        if any(query in str(f).lower() for f in p)]
        self.update_tree(filtered)

    def add_product(self):
        ProductEditWindow(self, self.db, self.refresh_products)

    def edit_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для редактирования.",
                                   parent=self)
            return
        item_vals = list(self.tree.item(selected[0])['values'])
        product = tuple(item_vals[1:])
        ProductEditWindow(self, self.db, self.refresh_products, product=product)

    def edit_selected(self):
        checked = self.tree.get_checked_iids()
        if not checked:
            messagebox.showwarning("Внимание",
                                   "Отметьте товары галочками для редактирования.",
                                   parent=self)
            return
        queue = []
        for iid in checked:
            if self.tree.exists(iid):
                vals = list(self.tree.item(iid, 'values'))
                queue.append(tuple(vals[1:]))
        if not queue:
            return
        self.edit_queue = queue
        self._open_next_edit()

    def _open_next_edit(self):
        if not self.edit_queue:
            return
        product = self.edit_queue.pop(0)
        ProductEditWindow(self, self.db, self.refresh_products,
                          product=product, on_saved=self._open_next_edit)

    def delete_selected(self):
        checked = self.tree.get_checked_iids()
        if not checked:
            messagebox.showwarning("Внимание",
                                   "Отметьте товары для удаления (колонка ☐).",
                                   parent=self)
            return
        names = [str(self.tree.item(iid, 'values')[3]) for iid in checked
                 if self.tree.exists(iid)]
        preview = ', '.join(names[:5])
        if len(names) > 5:
            preview += '...'
        msg = "Удалить {0} товаров?\n{1}".format(len(names), preview)
        if not messagebox.askyesno("Подтверждение", msg, parent=self):
            return
        for iid in checked:
            if not self.tree.exists(iid):
                continue
            vals = self.tree.item(iid, 'values')
            product_id = vals[1]
            try:
                self.db.delete_product(product_id)
            except Exception as e:
                messagebox.showerror("Ошибка",
                                     "Не удалось удалить товар: {0}".format(e),
                                     parent=self)
        self.refresh_products()

    def export_to_excel(self):
        checked = self.tree.get_checked_values()
        rows = checked if checked else [
            tuple(list(self.tree.item(iid, 'values'))[1:])
            for iid in self.tree.get_children('')]
        if not rows:
            messagebox.showwarning("Внимание", "Нет данных для экспорта.", parent=self)
            return
        headers = ["ID", "Код товара", "Наименование",
                   "Цена закупки", "Цена продажи", "Количество"]
        filepath = ExcelExporter.export_data(headers, rows, sheet_title="Склад")
        ExcelExporter.open_file(filepath)
        messagebox.showinfo("Экспорт", "Файл сохранён:\n" + filepath, parent=self)

    def on_filter_change(self):
        if self.available_var.get():
            if self.not_available_var.get():
                self.not_available_var.set(False)
            products = self.db.get_available_products()
        elif self.not_available_var.get():
            products = self.db.get_not_available_products()
        else:
            products = self.db.get_all_products()
        self.all_products = products
        self.update_tree(products)
        self.search_panel.clear()

    def on_close(self):
        self.edit_queue.clear()
        if hasattr(self.master, "child_windows") and self in self.master.child_windows:
            self.master.child_windows.remove(self)
        self.destroy()
