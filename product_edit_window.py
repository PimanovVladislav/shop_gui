import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
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
        self.icursor('@%d,%d' % (event.x, event.y))


class ProductEditWindow(tk.Toplevel):
    def __init__(self, master, db, refresh_callback, product=None, on_saved=None,
                 store=None):
        super().__init__(master)
        self.db = db
        self.store = store or getattr(master, 'product_store', None)
        self.refresh_callback = refresh_callback
        self.product = product
        self.on_saved = on_saved

        self.title("Редактирование товара" if product else "Добавление товара")
        self.geometry("400x380")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if product:
            full = self.store.get_db_row(product[0]) if self.store else db.get_product_by_id(product[0])
            if full:
                purchase_date = full[7] if len(full) > 7 and full[7] else None
            else:
                purchase_date = None
        else:
            purchase_date = None

        tk.Label(self, text="Наименование:").pack()
        self.name_var = tk.StringVar(value=product[2] if product else "")
        self.name_entry = tk.Entry(self, textvariable=self.name_var)
        self.name_entry.pack()
        bind_entry_shortcuts(self.name_entry)

        tk.Label(self, text="Код товара:").pack()
        self.code_var = tk.StringVar(value=product[1] if product else "")
        self.code_entry = tk.Entry(self, textvariable=self.code_var)
        self.code_entry.pack()
        bind_entry_shortcuts(self.code_entry)

        tk.Label(self, text="Цена закупки:").pack()
        self.buy_price_var = tk.DoubleVar(value=product[3] if product else 0.0)
        self._buy_price_entry = SelectAllEntry(self, textvariable=self.buy_price_var)
        self._buy_price_entry.pack()
        bind_entry_shortcuts(self._buy_price_entry)

        tk.Label(self, text="Цена продажи:").pack()
        self.sale_price_var = tk.DoubleVar(value=product[4] if product else 0.0)
        self._sale_price_entry = SelectAllEntry(self, textvariable=self.sale_price_var)
        self._sale_price_entry.pack()
        bind_entry_shortcuts(self._sale_price_entry)

        tk.Label(self, text="Количество:").pack()
        self.amount_var = tk.IntVar(value=product[5] if product else 0)
        self._amount_entry = SelectAllEntry(self, textvariable=self.amount_var)
        self._amount_entry.pack()
        bind_entry_shortcuts(self._amount_entry)

        tk.Label(self, text="Дата закупки:").pack()
        date_frame = tk.Frame(self)
        date_frame.pack()
        self.purchase_date = DateEntry(
            date_frame, locale="ru_RU", width=12,
            background="darkblue", foreground="white",
            borderwidth=2, date_pattern=DATE_PATTERN
        )
        self.purchase_date.pack()
        if purchase_date:
            d = parse_date(purchase_date)
            if d:
                self.purchase_date.set_date(d)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        if product is None:
            btn_add_more = tk.Button(btn_frame, text="Добавить ещё",
                                     command=self.save_and_continue)
            btn_add_more.pack(side=tk.LEFT, padx=5)

        btn_save = tk.Button(btn_frame, text="Сохранить", command=self.save)
        btn_save.pack(side=tk.LEFT, padx=5)

        center_window(self)
        self.after(50, self._focus_first_field)

    def _focus_first_field(self):
        try:
            self.name_entry.focus_force()
            self.name_entry.focus_set()
        except Exception:
            pass

    def _get_purchase_date_str(self):
        try:
            return self.purchase_date.get_date().strftime(DATE_FMT)
        except Exception:
            return None

    def _validate_and_collect(self):
        name = self.name_var.get().strip()
        code = self.code_var.get().strip()
        try:
            buy_price = float(self.buy_price_var.get())
            sale_price = float(self.sale_price_var.get())
            amount = int(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат числовых полей", parent=self)
            return None
        if not name:
            messagebox.showwarning("Внимание", "Наименование не может быть пустым", parent=self)
            return None
        if buy_price < 0 or sale_price < 0 or amount < 0:
            messagebox.showwarning("Внимание",
                                   "Числовые значения не могут быть отрицательными",
                                   parent=self)
            return None
        return (name, code, buy_price, sale_price, amount, self._get_purchase_date_str())

    def _clear_fields(self):
        self.name_var.set("")
        self.code_var.set("")
        self.buy_price_var.set(0.0)
        self.sale_price_var.set(0.0)
        self.amount_var.set(0)
        self.purchase_date.set_date(datetime.today())

    def save(self):
        data = self._validate_and_collect()
        if data is None:
            self._focus_first_field()
            return
        name, code, buy_price, sale_price, amount, purchase_date = data
        product_id = None
        if self.product:
            product_id = self.product[0]
            if self.store:
                self.store.update(
                    product_id, name, code, buy_price, sale_price, amount, purchase_date
                )
            else:
                c = self.db.conn.cursor()
                c.execute(
                    "UPDATE products SET name=?, code=?, buy_price=?, sale_price=?, "
                    "amount=?, purchase_date=? WHERE id=?",
                    (name, code, buy_price, sale_price, amount, purchase_date, product_id)
                )
                self.db.conn.commit()
        else:
            if self.store:
                product_id = self.store.add(
                    name, code, buy_price, sale_price, amount, purchase_date
                )
            else:
                product_id = self.db.add_product(
                    name, code, buy_price, sale_price, amount, purchase_date
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
        name, code, buy_price, sale_price, amount, purchase_date = data
        if self.store:
            product_id = self.store.add(
                name, code, buy_price, sale_price, amount, purchase_date
            )
        else:
            product_id = self.db.add_product(
                name, code, buy_price, sale_price, amount, purchase_date
            )
        self.refresh_callback(product_id)
        self._clear_fields()
        messagebox.showinfo("Готово", "Товар добавлен. Можно вводить следующий.",
                            parent=self)
        self._focus_first_field()

    def on_close(self):
        self.on_saved = None
        self.destroy()
