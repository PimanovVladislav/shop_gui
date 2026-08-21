import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from database_operation import Database
from product_edit_window import ProductEditWindow
from write_off_window import WriteOffWindow
from utils import SearchPanel, SortableTreeview, filter_with_checked, center_window, format_date, today_str
from excel_export import ExcelExporter


class WarehouseWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Склад")
        self.geometry("1000x500")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.all_products = []
        self.edit_queue = []
        self._focus_product_id = None

        self.search_panel = SearchPanel(self, self.on_search)
        self.search_panel.pack(fill=tk.X, padx=5, pady=5)
        self.search_panel.bind_shortcuts(self)

        self.tree = SortableTreeview(
            self,
            columns=('check', 'id', 'code', 'name', 'buy_price',
                     'sale_price', 'amount', 'purchase_date'),
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
        self.tree.heading('purchase_date', text='Дата закупки')

        self.tree.column('check', width=30, stretch=False)
        self.tree.column('id', width=50)
        self.tree.column('code', width=90)
        self.tree.column('name', width=180)
        self.tree.column('buy_price', width=90)
        self.tree.column('sale_price', width=90)
        self.tree.column('amount', width=80)
        self.tree.column('purchase_date', width=100)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.tree.setup_sorting()

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="Добавить товар",
                  command=self.add_product).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Редактировать выбранные",
                  command=self.edit_selected).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Списать",
                  command=self.write_off_product).pack(side=tk.LEFT, padx=2)
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

        center_window(self)
        self.refresh_products()

    def refresh_products(self, focus_product_id=None):
        if focus_product_id is not None:
            self._focus_product_id = focus_product_id
        self.all_products = self.db.get_all_products()
        self._apply_filter_and_display(clear_search=True)

    def _apply_filter_and_display(self, query='', clear_search=False):
        if self.available_var.get():
            base = self.db.get_available_products()
        elif self.not_available_var.get():
            base = self.db.get_not_available_products()
        else:
            base = self.all_products

        checked_keys = set(self.tree.get_checked_iids())
        query = query.strip().lower()

        if not query:
            products = base
        else:
            search_col = self.tree.get_search_column()
            mapping = {'id': 0, 'code': 1, 'name': 2, 'buy_price': 3,
                       'sale_price': 4, 'amount': 5, 'purchase_date': 6}

            def match(p):
                if search_col is not None and search_col in mapping:
                    idx = mapping[search_col]
                    return idx < len(p) and query in str(p[idx]).lower()
                return any(query in str(f).lower() for f in p)

            products = filter_with_checked(
                base, checked_keys, match, lambda p: str(p[0])
            )

        self.update_tree(products)
        if clear_search:
            self.search_panel.clear()

    def update_tree(self, products):
        self.tree.delete(*self.tree.get_children())
        for p in products:
            display = list(p)
            if len(display) > 6:
                if display[6] is None or display[6] == '':
                    display[6] = '—'
                else:
                    display[6] = format_date(display[6])
            self.tree.insert('', 'end', iid=str(p[0]), values=display)
        self.tree.restore_checks()
        self.tree.move_checked_to_top()
        if self._focus_product_id is not None:
            iid = str(self._focus_product_id)
            if self.tree.exists(iid):
                self.tree.selection_set([iid])
                self.tree.set_active(iid)
                self.tree.see(iid)
                self.tree.tree.focus_set()
            self._focus_product_id = None

    def on_search(self, query):
        self._apply_filter_and_display(query)

    def add_product(self):
        ProductEditWindow(self, self.db, self.refresh_products)

    def edit_selected(self):
        checked = self.tree.get_checked_iids()
        if checked:
            iids = [iid for iid in checked if self.tree.exists(iid)]
        else:
            focused = self.tree.get_focused_row_iid()
            if not focused:
                messagebox.showwarning(
                    "Внимание",
                    "Отметьте товары галочками или выберите строку для редактирования.",
                    parent=self)
                return
            iids = [focused]
        queue = []
        for iid in iids:
            product_id = int(iid)
            product = self.db.get_product_by_id(product_id)
            if product:
                queue.append((
                    product[0], product[2], product[1],
                    product[3], product[4], product[5]
                ))
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

    def write_off_product(self):
        selected = self.tree.selection()
        checked = self.tree.get_checked_iids()
        product_id = None
        if len(checked) == 1:
            product_id = int(checked[0])
        elif selected:
            product_id = int(selected[0])
        if product_id is None:
            messagebox.showwarning(
                "Внимание", "Выберите один товар для списания.", parent=self)
            return
        WriteOffWindow(self, self.db, product_id, self.refresh_products)

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
        if not messagebox.askyesno("Подтверждение",
                                   f"Удалить {len(names)} товаров?\n{preview}",
                                   parent=self):
            return
        for iid in checked:
            if not self.tree.exists(iid):
                continue
            try:
                self.db.delete_product(int(iid))
            except Exception as e:
                messagebox.showerror("Ошибка",
                                     f"Не удалось удалить товар: {e}", parent=self)
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
                   "Цена закупки", "Цена продажи", "Количество", "Дата закупки"]
        filename = f"Склад_{today_str()}.xlsx"
        filepath = ExcelExporter.export_data(
            headers, rows, filename=filename, sheet_title="Склад")
        ExcelExporter.open_file(filepath)
        messagebox.showinfo("Экспорт", f"Файл сохранён:\n{filepath}", parent=self)

    def on_filter_change(self):
        if self.available_var.get() and self.not_available_var.get():
            self.not_available_var.set(False)
        self._apply_filter_and_display(clear_search=True)

    def on_close(self):
        self.edit_queue.clear()
        if hasattr(self.master, "child_windows") and self in self.master.child_windows:
            self.master.child_windows.remove(self)
        self.destroy()
