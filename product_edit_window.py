import tkinter as tk
from tkinter import messagebox


class SelectAllEntry(tk.Entry):
    """Entry, выделяющий весь текст при клике (одинарном). При двойном — курсор на месте."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<Button-1>', self._on_single_click)
        # Двойной клик не трогаем — стандартное поведение ставит курсор

    def _on_single_click(self, event):
        """Выделить всё содержимое."""
        self.after(0, lambda: self.select_range(0, tk.END))
        # Возвращаем 'break' чтобы предотвратить снятие выделения
        # Но это сломает фокус. Поэтому используем after + ручной return
        return None


class ProductEditWindow(tk.Toplevel):
    def __init__(self, master, db, refresh_callback, product=None):
        super().__init__(master)
        self.db = db
        self.refresh_callback = refresh_callback
        self.product = product

        self.title("Редактирование товара" if product else "Добавление товара")
        self.geometry("400x300")
        self.wm_iconbitmap("main_icon.ico")

        # Наименование (обычный Entry)
        tk.Label(self, text="Наименование:").pack()
        self.name_var = tk.StringVar(value=product[1] if product else "")
        tk.Entry(self, textvariable=self.name_var).pack()

        # Код товара (обычный Entry)
        tk.Label(self, text="Код товара:").pack()
        self.code_var = tk.StringVar(value=product[2] if product else "")
        tk.Entry(self, textvariable=self.code_var).pack()

        # Цена закупки (SelectAllEntry)
        tk.Label(self, text="Цена закупки:").pack()
        self.buy_price_var = tk.DoubleVar(value=product[3] if product else 0.0)
        self._buy_price_entry = SelectAllEntry(self, textvariable=self.buy_price_var)
        self._buy_price_entry.pack()

        # Цена продажи (SelectAllEntry)
        tk.Label(self, text="Цена продажи:").pack()
        self.sale_price_var = tk.DoubleVar(value=product[4] if product else 0.0)
        self._sale_price_entry = SelectAllEntry(self, textvariable=self.sale_price_var)
        self._sale_price_entry.pack()

        # Количество (SelectAllEntry)
        tk.Label(self, text="Количество:").pack()
        self.amount_var = tk.IntVar(value=product[5] if product else 0)
        self._amount_entry = SelectAllEntry(self, textvariable=self.amount_var)
        self._amount_entry.pack()

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        if product is None:
            btn_add_more = tk.Button(btn_frame, text="Добавить ещё",
                                     command=self.save_and_continue)
            btn_add_more.pack(side=tk.LEFT, padx=5)

        btn_save = tk.Button(btn_frame, text="Сохранить", command=self.save)
        btn_save.pack(side=tk.LEFT, padx=5)

    def _validate_and_collect(self):
        name = self.name_var.get().strip()
        code = self.code_var.get().strip()
        try:
            buy_price = float(self.buy_price_var.get())
            sale_price = float(self.sale_price_var.get())
            amount = int(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат числовых полей")
            return None
        if not name:
            messagebox.showwarning("Внимание", "Наименование не может быть пустым")
            return None
        if buy_price < 0 or sale_price < 0 or amount < 0:
            messagebox.showwarning("Внимание",
                                   "Числовые значения не могут быть отрицательными")
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
            return
        name, code, buy_price, sale_price, amount = data
        self.db.add_product(name, code, buy_price, sale_price, amount)
        self.refresh_callback()
        self._clear_fields()
        messagebox.showinfo("Готово", "Товар добавлен. Можно вводить следующий.")
