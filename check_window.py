import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from domain.constants import CHECK_STATUS_SALE
from receipt_window import ReceiptWindow
from resources.i18n import check_status_label, t
from utils import SortableTreeview, SearchPanel, center_window, setup_table_navigation, unregister_table_navigation


class ChecksWindow(tk.Toplevel):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.title(t('checks.title'))
        self.geometry('1200x550')
        self.state('zoomed')
        self.wm_iconbitmap('main_icon.ico')
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        style = ttk.Style(self)
        style.configure('Treeview.Heading',
                        font=('TkDefaultFont', 9, 'bold'), padding=(5, 8))

        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.search_panel = SearchPanel(main_frame, self.on_search)
        self.search_panel.pack(fill=tk.X, padx=5, pady=5)
        self.search_panel.bind_shortcuts(self)

        left_panel = tk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.checks_tree = SortableTreeview(
            left_panel,
            columns=('id', 'date', 'status', 'payment_type',
                     'sum', 'payed_sum', 'refused_sum'),
            show='headings',
            checkbox_column=False
        )
        col_widths = {'id': 50, 'date': 130, 'status': 120,
                      'payment_type': 100, 'sum': 80,
                      'payed_sum': 80, 'refused_sum': 80}
        headers = [
            ('id', t('checks.col.id')),
            ('date', t('checks.col.date')),
            ('status', t('checks.col.status')),
            ('payment_type', t('checks.col.payment_type')),
            ('sum', t('checks.col.sum')),
            ('payed_sum', t('checks.col.payed')),
            ('refused_sum', t('checks.col.refused')),
        ]
        for col, colname in headers:
            self.checks_tree.heading(col, text=colname)
            self.checks_tree.column(col, width=col_widths[col], anchor=tk.CENTER)
        self.checks_tree.setup_sorting()
        self.checks_tree.bind('<<TreeviewSelect>>', self.on_check_selected)
        self.checks_tree.pack(fill=tk.BOTH, expand=True)

        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cols = ('check', 'name', 'code', 'amount', 'price', 'total_price')
        self.products_tree = SortableTreeview(
            right_panel,
            columns=cols,
            show='headings',
            checkbox_column=True,
            double_click_check=False
        )
        self.products_tree.heading('check', text=t('common.checkbox_header'))
        self.products_tree.heading('name', text=t('checks.product.name'))
        self.products_tree.heading('code', text=t('checks.product.code'))
        self.products_tree.heading('amount', text=t('checks.product.amount'))
        self.products_tree.heading('price', text=t('checks.product.price'))
        self.products_tree.heading('total_price', text=t('checks.product.total'))
        self.products_tree.column('check', width=30, stretch=False)
        self.products_tree.column('name', width=180)
        self.products_tree.column('code', width=60)
        self.products_tree.column('amount', width=70, anchor=tk.CENTER)
        self.products_tree.column('price', width=80, anchor=tk.E)
        self.products_tree.column('total_price', width=80, anchor=tk.E)
        self.products_tree.setup_sorting()
        self.products_tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(right_panel)
        btn_frame.pack(fill=tk.X, pady=5)

        self.btn_return_selected = tk.Button(
            btn_frame, text=t('checks.btn.return_selected'),
            command=self.return_selected_products)
        self.btn_return_selected.pack(side=tk.LEFT, padx=5)

        self.btn_return_all = tk.Button(
            btn_frame, text=t('checks.btn.return_all'),
            command=self.return_entire_check)
        self.btn_return_all.pack(side=tk.LEFT, padx=5)

        self.btn_open_receipt = tk.Button(
            btn_frame, text=t('checks.btn.open_receipt'),
            command=self.open_receipt)
        self.btn_open_receipt.pack(side=tk.LEFT, padx=5)

        self.current_check_id = None
        self.all_checks = []

        self.products_tree.bind('<Double-1>', self.on_product_double_click)
        self.products_tree.tag_configure('selected', background='#d3d3d3')

        setup_table_navigation(self, [self.checks_tree, self.products_tree], horizontal=True)

        self.refresh_checks()
        center_window(self)

    def refresh_checks(self):
        self.all_checks = self.db.get_all_checks()
        self._display_checks(self.all_checks)
        self.products_tree.delete(*self.products_tree.get_children())

    def _check_row_values(self, r):
        return (
            r[0], r[1], check_status_label(r[2]),
            r[3], f'{r[4]:.2f}', f'{r[5]:.2f}', f'{r[6]:.2f}'
        )

    def _display_checks(self, rows):
        display = [(None, self._check_row_values(r)) for r in rows]
        self.checks_tree.load_rows(
            display,
            iid_fn=lambda row: None,
            values_fn=lambda row: row[1],
            restore_checked=False,
        )

    def _get_check_status(self, check_id):
        for row in self.all_checks:
            if row[0] == check_id:
                return row[2]
        return None

    def on_check_selected(self, event):
        selected = self.checks_tree.selection()
        if not selected:
            return
        self.current_check_id = self.checks_tree.item(selected[0])['values'][0]
        is_sale = self._get_check_status(self.current_check_id) == CHECK_STATUS_SALE
        self.btn_return_selected.config(state='normal' if is_sale else 'disabled')
        self.btn_return_all.config(state='normal' if is_sale else 'disabled')
        self.refresh_products(self.current_check_id)

    def refresh_products(self, check_id):
        rows = self.db.checks.get_check_products(check_id)
        display = []
        for r in rows:
            cp_id, _product_id, name, code, amount, price = r
            total_price = price * amount
            display.append((
                str(cp_id),
                (name, code, amount, f'{price:.2f}', f'{total_price:.2f}')
            ))
        self.products_tree.load_rows(
            display,
            iid_fn=lambda row: row[0],
            values_fn=lambda row: row[1],
        )

    def on_product_double_click(self, event):
        region = self.products_tree.identify('region', event.x, event.y)
        if region != 'cell':
            return
        rowid = self.products_tree.identify_row(event.y)
        column = self.products_tree.identify_column(event.x)
        if not rowid or not column:
            return
        col_num = int(column.replace('#', ''))
        if col_num == 4:
            current_vals = self.products_tree.item(rowid, 'values')
            current_amount = current_vals[3]
            new_amount = simpledialog.askinteger(
                t('checks.return_qty_title'),
                t('checks.return_qty_prompt', max=current_amount),
                minvalue=0, maxvalue=int(current_amount), parent=self
            )
            if new_amount is None:
                return
            price = float(current_vals[4])
            total_price = price * new_amount
            new_vals = list(current_vals)
            new_vals[3] = new_amount
            new_vals[5] = f'{total_price:.2f}'
            self.products_tree.item(rowid, values=new_vals)

    def open_receipt(self):
        if not self.current_check_id:
            messagebox.showwarning(t('common.attention'), t('checks.select_check'),
                                   parent=self)
            return
        row = self.db.get_receipt_text(self.current_check_id)
        if row is None:
            messagebox.showwarning(t('common.attention'), t('payment.no_receipt_text'),
                                   parent=self)
            return
        date_str, receipt_text = row
        if not receipt_text:
            messagebox.showwarning(t('common.attention'), t('payment.no_receipt_text'),
                                   parent=self)
            return
        ReceiptWindow(self, self.current_check_id, date_str, receipt_text)

    def return_selected_products(self):
        if not self.current_check_id:
            messagebox.showwarning(t('common.attention'), t('checks.select_check'),
                                   parent=self)
            return
        checked = self.products_tree.get_checked_iids()
        if not checked:
            messagebox.showwarning(t('common.attention'), t('checks.select_products'),
                                   parent=self)
            return

        items = []
        for cp_id in checked:
            vals = self.products_tree.item(cp_id, 'values')
            amount_to_return = int(vals[3])
            if amount_to_return <= 0:
                continue
            product_id = self.db.checks.get_product_id_for_check_product(cp_id)
            if product_id is None:
                continue
            items.append((cp_id, product_id, amount_to_return, float(vals[4])))

        if not items:
            return

        try:
            new_check_id, total_refund_sum, store_deltas = self.db.checks.create_return(
                self.current_check_id, items
            )
        except ValueError as e:
            messagebox.showerror(t('common.error'), str(e), parent=self)
            return

        store = getattr(self.master, 'product_store', None)
        if store:
            store.apply_amount_deltas(store_deltas)

        messagebox.showinfo(
            t('common.success'),
            t('checks.return_success', id=new_check_id, sum=f'{total_refund_sum:.2f}'),
            parent=self)
        self.refresh_checks()

    def return_entire_check(self):
        if not self.current_check_id:
            messagebox.showwarning(t('common.attention'), t('checks.select_check'),
                                   parent=self)
            return

        rows = self.db.checks.get_check_products(self.current_check_id)
        items = []
        for cp_id, product_id, _name, _code, amount, price in rows:
            if amount <= 0:
                continue
            items.append((str(cp_id), product_id, amount, price))

        if not items:
            return

        try:
            new_check_id, total_refund_sum, store_deltas = self.db.checks.create_return(
                self.current_check_id, items
            )
        except ValueError as e:
            messagebox.showerror(t('common.error'), str(e), parent=self)
            return

        store = getattr(self.master, 'product_store', None)
        if store:
            store.apply_amount_deltas(store_deltas)

        messagebox.showinfo(
            t('common.success'),
            t('checks.return_success', id=new_check_id, sum=f'{total_refund_sum:.2f}'),
            parent=self)
        self.refresh_checks()

    def on_search(self, query):
        query = query.strip().lower()
        if not query:
            filtered = self.all_checks
        else:
            filtered = []
            for r in self.all_checks:
                id_str = str(r[0])
                date_str = (r[1] or '').lower()
                status_str = check_status_label(r[2]).lower()
                payment_str = (r[3] or '').lower()
                if (query in id_str or query in date_str or
                        query in status_str or query in payment_str):
                    filtered.append(r)
        self._display_checks(filtered)
        self.products_tree.delete(*self.products_tree.get_children())

    def on_close(self):
        unregister_table_navigation(self)
        if hasattr(self.master, 'child_windows') and self in self.master.child_windows:
            self.master.child_windows.remove(self)
        self.destroy()
