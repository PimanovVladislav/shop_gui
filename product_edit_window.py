import tkinter as tk
from tkinter import messagebox
from utils import bind_entry_shortcuts


class SelectAllEntry(tk.Entry):
    """Entry: одинарный клик выделяет весь текст, двойной ставит курсор."""

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
    def __init__(self, master, db, refresh_callback, product=None):
        super().__init__(master)
        self.db = db
        self.refresh_callback = refresh_callback
        self.product = product

        self.title("Редактирование товара" if product else "Добавление товара")
        self.geometry("400x300")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        if product is None:
            btn_add_more = tk.Button(btn_frame, text="Добавить ещё",
                                     command=self.save_and_continue)
            btn_add_more.pack(side=tk.LEFT, padx=5)

        btn_save = tk.Button(btn_frame, text="Сохранить", command=self.save)
        btn_save.pack(side=tk.LEFT, padx=5)

        # Фокус на первое поле после показа окна
        self.after(50, self._focus_first_field)

    def _focus_first_field(self):
        """Возвращает фокус на первое поле ввода этого окна."""
        try:
            self.name_entry.focus_force()
            self.name_entry.focus_set()
        except Exception:
            pass
        try:
            self.lift()
        except Exception:
            pass

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
        return (name, code, buy_price, sale_price, amount)

    def _clear_fields(self):
        self.name_var.set("")
        self.code_var.set("")
        self.buy_price_var.set(0.0)
        self.sale_price_var.set(0.0)
        self.amount_var.set(0)

    def save(self):
        data = self._validate_and_collect()
        if data is None:
            self._focus_first_field()
            return
        name, code, buy_price, sale_price, amount = data
        if self.product:
            c = self.db.conn.cursor()
            c.execute(
                "UPDATE products SET name=?, code=?, buy_price=?, sale_price=?, amount=? "
                "WHERE id=?",
                (name, code, buy_price, sale_price, amount, self.product[0])
            )
            self.db.conn.commit()
        else:
            self.db.add_product(name, code, buy_price, sale_price, amount)
        self.refresh_callback()
        self.destroy()

    def save_and_continue(self):
        data = self._validate_and_collect()
        if data is None:
            self._focus_first_field()
            return
        name, code, buy_price, sale_price, amount = data
        self.db.add_product(name, code, buy_price, sale_price, amount)
        self.refresh_callback()
        self._clear_fields()
        # Возвращаем фокус этому окну (а не главному)
        self._focus_first_field()
        messagebox.showinfo("Готово", "Товар добавлен. Можно вводить следующий.", parent=self)
        self._focus_first_field()

    def on_close(self):
        self.destroy()
