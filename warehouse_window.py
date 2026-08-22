import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from database_operation import Database
from product_edit_window import ProductEditWindow
from write_off_window import WriteOffWindow
from config.paths import resource_path
from resources.i18n import t
from utils import SearchPanel, SortableTreeview, filter_with_checked, center_window, format_date, today_str, setup_table_navigation, unregister_table_navigation
from excel_export import ExcelExporter


class WarehouseWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.store = master.product_store
        self.title(t('warehouse.title'))
        self.geometry("1000x500")
        self.state('zoomed')
        self.wm_iconbitmap(resource_path('main_icon.ico'))
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
                     'sale_price', 'amount', 'purchase_date', 'supplier'),
            show='headings',
            checkbox_column=True
        )
        self.tree.heading('check', text=t('common.checkbox_header'))
        self.tree.heading('id', text=t('warehouse.col.id'))
        self.tree.heading('code', text=t('warehouse.col.code'))
        self.tree.heading('name', text=t('warehouse.col.name'))
        self.tree.heading('buy_price', text=t('warehouse.col.buy_price'))
        self.tree.heading('sale_price', text=t('warehouse.col.sale_price'))
        self.tree.heading('amount', text=t('warehouse.col.amount'))
        self.tree.heading('purchase_date', text=t('warehouse.col.purchase_date'))
        self.tree.heading('supplier', text=t('warehouse.col.supplier'))

        self.tree.column('check', width=30, stretch=False)
        self.tree.column('id', width=50)
        self.tree.column('code', width=90)
        self.tree.column('name', width=180)
        self.tree.column('buy_price', width=90)
        self.tree.column('sale_price', width=90)
        self.tree.column('amount', width=80)
        self.tree.column('purchase_date', width=100)
        self.tree.column('supplier', width=140)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.tree.setup_sorting()

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text=t('warehouse.btn.add'),
                  command=self.add_product).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text=t('warehouse.btn.edit_selected'),
                  command=self.edit_selected).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text=t('warehouse.btn.write_off'),
                  command=self.write_off_product).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text=t('warehouse.btn.refresh'),
                  command=self.refresh_products).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text=t('warehouse.btn.delete'),
                  command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text=t('warehouse.btn.export'),
                  command=self.export_to_excel).pack(side=tk.LEFT, padx=2)

        self.available_var = tk.BooleanVar(value=False)
        self.not_available_var = tk.BooleanVar(value=False)

        tk.Checkbutton(btn_frame, text=t('warehouse.filter.available'),
                       variable=self.available_var,
                       command=self.on_filter_change).pack(
            side=tk.LEFT, padx=(20, 5))
        tk.Checkbutton(btn_frame, text=t('warehouse.filter.not_available'),
                       variable=self.not_available_var,
                       command=self.on_filter_change).pack(
            side=tk.LEFT, padx=5)

        setup_table_navigation(self, [self.tree])

        center_window(self)
        self.refresh_products()

    def _format_product_values(self, p):
        display = list(p)
        if len(display) > 6:
            if display[6] is None or display[6] == '':
                display[6] = t('common.dash')
            else:
                display[6] = format_date(display[6])
        if len(display) > 7:
            if display[7] is None or display[7] == '':
                display[7] = t('common.dash')
        return tuple(display)

    def refresh_products(self, focus_product_id=None):
        if focus_product_id is not None:
            self._focus_product_id = focus_product_id
            if self._update_single_product(focus_product_id):
                return
        self.store.reload()
        self.all_products = self.store.get_all()
        self._apply_filter_and_display(clear_search=focus_product_id is not None)

    def _update_single_product(self, product_id):
        p = self.store.get(product_id)
        iid = str(product_id)
        if p is None:
            if self.tree.exists(iid):
                self.tree.delete(iid)
            self.all_products = self.store.get_all()
            return True
        if not self._product_matches_filter(p):
            self.all_products = self.store.get_all()
            self._apply_filter_and_display()
            return True
        values = self._format_product_values(p)
        if self.tree.exists(iid):
            self.tree.item(iid, values=values)
            for i, row in enumerate(self.all_products):
                if row[0] == product_id:
                    self.all_products[i] = p
                    break
            if self._focus_product_id is not None:
                self.tree.set_active(iid)
                self.tree.see(iid)
                self.tree.tree.focus_set()
                self._focus_product_id = None
            return True
        self.all_products = self.store.get_all()
        self._apply_filter_and_display()
        return True

    def _product_matches_filter(self, p):
        if self.available_var.get() and p[5] <= 0:
            return False
        if self.not_available_var.get() and p[5] != 0:
            return False
        return True

    def _apply_filter_and_display(self, query='', clear_search=False):
        if self.available_var.get():
            base = self.store.get_available()
        elif self.not_available_var.get():
            base = self.store.get_not_available()
        else:
            base = self.all_products

        checked_keys = set(self.tree.get_checked_iids())
        query = query.strip().lower()

        if not query:
            products = base
        else:
            search_col = self.tree.get_search_column()
            mapping = {'id': 0, 'code': 1, 'name': 2, 'buy_price': 3,
                       'sale_price': 4, 'amount': 5, 'purchase_date': 6,
                       'supplier': 7}

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
        rows = [(str(p[0]), self._format_product_values(p)) for p in products]
        self.tree.load_rows(
            rows,
            iid_fn=lambda row: row[0],
            values_fn=lambda row: row[1],
        )
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
        ProductEditWindow(self, self.db, self.refresh_products, store=self.store)

    def edit_selected(self):
        checked = self.tree.get_checked_iids()
        if checked:
            iids = [iid for iid in checked if self.tree.exists(iid)]
        else:
            focused = self.tree.get_focused_row_iid()
            if not focused:
                messagebox.showwarning(
                    t('common.attention'),
                    t('warehouse.edit_no_selection'),
                    parent=self)
                return
            iids = [focused]
        queue = []
        for iid in iids:
            product_id = int(iid)
            product = self.store.get_db_row(product_id)
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
                          product=product, on_saved=self._open_next_edit,
                          store=self.store)

    def write_off_product(self):
        selected = self.tree.selection()
        checked = self.tree.get_checked_iids()
        product_id = None
        if len(checked) == 1:
            product_id = int(checked[0])
        elif selected:
            product_id = int(selected[0])
        if product_id is None:
            focused = self.tree.get_focused_row_iid()
            if focused:
                product_id = int(focused)
        if product_id is None:
            messagebox.showwarning(
                t('common.attention'), t('warehouse.write_off_select_one'), parent=self)
            return
        WriteOffWindow(self, self.db, product_id, self.refresh_products,
                       store=self.store)

    def delete_selected(self):
        checked = self.tree.get_checked_iids()
        if not checked:
            messagebox.showwarning(t('common.attention'),
                                   t('warehouse.delete_no_selection'),
                                   parent=self)
            return
        names = [str(self.tree.item(iid, 'values')[3]) for iid in checked
                 if self.tree.exists(iid)]
        preview = ', '.join(names[:5])
        if len(names) > 5:
            preview += '...'
        if not messagebox.askyesno(t('common.confirm'),
                                   t('warehouse.delete_confirm',
                                     count=len(names), preview=preview),
                                   parent=self):
            return
        for iid in checked:
            if not self.tree.exists(iid):
                continue
            try:
                self.store.delete(int(iid))
            except Exception as e:
                messagebox.showerror(t('common.error'),
                                     t('warehouse.delete_error', error=e), parent=self)
        self.refresh_products()

    def export_to_excel(self):
        checked = self.tree.get_checked_values()
        rows = checked if checked else [
            tuple(list(self.tree.item(iid, 'values'))[1:])
            for iid in self.tree.get_children('')]
        if not rows:
            messagebox.showwarning(t('common.attention'), t('warehouse.export_no_data'),
                                   parent=self)
            return
        headers = [
            t('warehouse.col.id'), t('warehouse.col.code'), t('warehouse.col.name'),
            t('warehouse.col.buy_price'), t('warehouse.col.sale_price'),
            t('warehouse.col.amount'), t('warehouse.col.purchase_date'),
            t('warehouse.col.supplier'),
        ]
        filename = t('warehouse.export_filename', date=today_str())
        filepath = ExcelExporter.export_data(
            headers, rows, filename=filename, sheet_title=t('warehouse.export_sheet'))
        ExcelExporter.open_file(filepath)
        messagebox.showinfo(t('common.export'), t('warehouse.export_saved', path=filepath),
                            parent=self)

    def on_filter_change(self):
        if self.available_var.get() and self.not_available_var.get():
            self.not_available_var.set(False)
        self._apply_filter_and_display(clear_search=True)

    def on_close(self):
        unregister_table_navigation(self)
        self.edit_queue.clear()
        if hasattr(self.master, "child_windows") and self in self.master.child_windows:
            self.master.child_windows.remove(self)
        self.destroy()
