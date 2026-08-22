import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime

from config.paths import resource_path
from resources.i18n import t
from utils import bind_entry_shortcuts, center_window, DATE_PATTERN, DATE_FMT, parse_date, format_date


class SelectAllEntry(tk.Entry):
    """Entry: single click selects all text, double click places cursor."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self._after_id = None
        self.bind('<Button-1>', self._on_click)
        self.bind('<Double-1>', self._on_double)

    def _on_click(self, event):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(200, self._select_all_delayed)

    def _select_all_delayed(self):
        self._after_id = None
        self.select_range(0, tk.END)

    def _on_double(self, event):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.select_clear()
        try:
            self.icursor(self.index(f"@{event.x},{event.y}"))
        except tk.TclError:
            self.icursor(tk.END)
        return 'break'


class ProductEditWindow(tk.Toplevel):
    def __init__(self, master, db, refresh_callback, product=None, on_saved=None,
                 store=None):
        super().__init__(master)
        self.db = db
        self.store = store or getattr(master, 'product_store', None)
        self.refresh_callback = refresh_callback
        self.product = product
        self.on_saved = on_saved

        self.title(t('product_edit.title.edit') if product else t('product_edit.title.add'))
        self.geometry("400x430")
        self.wm_iconbitmap(resource_path('main_icon.ico'))
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if product:
            full = self.store.get_db_row(product[0]) if self.store else db.get_product_by_id(product[0])
            if full:
                purchase_date = full[7] if len(full) > 7 and full[7] else None
                supplier = full[8] if len(full) > 8 and full[8] else ''
            else:
                purchase_date = None
                supplier = ''
        else:
            purchase_date = None
            supplier = ''

        tk.Label(self, text=t('product_edit.label.name')).pack()
        self.name_var = tk.StringVar(value=product[2] if product else "")
        self.name_entry = tk.Entry(self, textvariable=self.name_var)
        self.name_entry.pack()
        bind_entry_shortcuts(self.name_entry)

        tk.Label(self, text=t('product_edit.label.code')).pack()
        self.code_var = tk.StringVar(value=product[1] if product else "")
        self.code_entry = tk.Entry(self, textvariable=self.code_var)
        self.code_entry.pack()
        bind_entry_shortcuts(self.code_entry)

        tk.Label(self, text=t('product_edit.label.buy_price')).pack()
        self.buy_price_var = tk.DoubleVar(value=product[3] if product else 0.0)
        self._buy_price_entry = SelectAllEntry(self, textvariable=self.buy_price_var)
        self._buy_price_entry.pack()
        bind_entry_shortcuts(self._buy_price_entry)

        tk.Label(self, text=t('product_edit.label.sale_price')).pack()
        self.sale_price_var = tk.DoubleVar(value=product[4] if product else 0.0)
        self._sale_price_entry = SelectAllEntry(self, textvariable=self.sale_price_var)
        self._sale_price_entry.pack()
        bind_entry_shortcuts(self._sale_price_entry)

        tk.Label(self, text=t('product_edit.label.amount')).pack()
        self.amount_var = tk.IntVar(value=product[5] if product else 0)
        self._amount_entry = SelectAllEntry(self, textvariable=self.amount_var)
        self._amount_entry.pack()
        bind_entry_shortcuts(self._amount_entry)

        tk.Label(self, text=t('product_edit.label.purchase_date')).pack()
        date_frame = tk.Frame(self)
        date_frame.pack()
        self.purchase_date = DateEntry(
            date_frame, locale="ru_RU", width=12,
            background="darkblue", foreground="white",
            borderwidth=2, date_pattern=DATE_PATTERN
        )
        self.purchase_date.pack(side=tk.LEFT)

        has_date = bool(purchase_date) and parse_date(purchase_date) is not None
        self.empty_date_var = tk.BooleanVar(value=not has_date)
        self.empty_date_cb = tk.Checkbutton(
            date_frame, text=t('product_edit.empty_date'),
            variable=self.empty_date_var,
            command=self._on_empty_date_toggle
        )
        self.empty_date_cb.pack(side=tk.LEFT, padx=(8, 0))

        if has_date:
            self.purchase_date.set_date(parse_date(purchase_date))
        else:
            self.purchase_date.set_date(datetime.today())
        self._on_empty_date_toggle()

        tk.Label(self, text=t('product_edit.label.supplier')).pack()
        self.supplier_var = tk.StringVar(value=supplier)
        self.supplier_entry = tk.Entry(self, textvariable=self.supplier_var)
        self.supplier_entry.pack(fill=tk.X, padx=20)
        bind_entry_shortcuts(self.supplier_entry)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        if product is None:
            btn_add_more = tk.Button(btn_frame, text=t('product_edit.btn.add_more'),
                                     command=self.save_and_continue)
            btn_add_more.pack(side=tk.LEFT, padx=5)

        btn_save = tk.Button(btn_frame, text=t('common.save'), command=self.save)
        btn_save.pack(side=tk.LEFT, padx=5)

        center_window(self)
        self.after(50, self._focus_first_field)

    def _focus_first_field(self):
        try:
            self.name_entry.focus_force()
            self.name_entry.focus_set()
        except Exception:
            pass

    def _on_empty_date_toggle(self):
        if self.empty_date_var.get():
            self.purchase_date.config(state='disabled')
        else:
            self.purchase_date.config(state='normal')

    def _get_purchase_date_str(self):
        if self.empty_date_var.get():
            return None
        try:
            return self.purchase_date.get_date().strftime(DATE_FMT)
        except Exception:
            return None

    def _validate_and_collect(self):
        name = self.name_var.get().strip()
        code = self.code_var.get().strip()
        supplier = self.supplier_var.get().strip()
        try:
            buy_price = float(self.buy_price_var.get())
            sale_price = float(self.sale_price_var.get())
            amount = int(self.amount_var.get())
        except ValueError:
            messagebox.showerror(t('common.error'), t('product_edit.invalid_numbers'), parent=self)
            return None
        if not name:
            messagebox.showwarning(t('common.attention'), t('product_edit.empty_name'), parent=self)
            return None
        if buy_price < 0 or sale_price < 0 or amount < 0:
            messagebox.showwarning(t('common.attention'), t('product_edit.negative_values'),
                                   parent=self)
            return None
        return (name, code, buy_price, sale_price, amount,
                self._get_purchase_date_str(), supplier)

    def _clear_fields(self):
        self.name_var.set("")
        self.code_var.set("")
        self.buy_price_var.set(0.0)
        self.sale_price_var.set(0.0)
        self.amount_var.set(0)
        self.purchase_date.set_date(datetime.today())
        self.empty_date_var.set(True)
        self._on_empty_date_toggle()
        self.supplier_var.set("")

    def save(self):
        data = self._validate_and_collect()
        if data is None:
            self._focus_first_field()
            return
        name, code, buy_price, sale_price, amount, purchase_date, supplier = data
        product_id = None
        if self.product:
            product_id = self.product[0]
            if self.store:
                self.store.update(
                    product_id, name, code, buy_price, sale_price, amount,
                    purchase_date, supplier
                )
            else:
                self.db.products.update(
                    product_id, name, code, buy_price, sale_price, amount,
                    purchase_date, supplier
                )
        else:
            if self.store:
                product_id = self.store.add(
                    name, code, buy_price, sale_price, amount, purchase_date, supplier
                )
            else:
                product_id = self.db.add_product(
                    name, code, buy_price, sale_price, amount, purchase_date, supplier
                )
        self.refresh_callback(product_id)
        cb = self.on_saved
        self.on_saved = None
        self.destroy()
        if cb:
            cb()

    def save_and_continue(self):
        data = self._validate_and_collect()
        if data is None:
            self._focus_first_field()
            return
        name, code, buy_price, sale_price, amount, purchase_date, supplier = data
        if self.store:
            product_id = self.store.add(
                name, code, buy_price, sale_price, amount, purchase_date, supplier
            )
        else:
            product_id = self.db.add_product(
                name, code, buy_price, sale_price, amount, purchase_date, supplier
            )
        self.refresh_callback(product_id)
        self._clear_fields()
        messagebox.showinfo(t('common.ready'), t('product_edit.added_continue'),
                            parent=self)
        self._focus_first_field()

    def on_close(self):
        self.on_saved = None
        self.destroy()
