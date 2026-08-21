import tkinter as tk
from tkinter import messagebox
from utils import center_window, bind_entry_shortcuts, format_date


class WheelSpinbox(tk.Spinbox):
    """Spinbox с поддержкой колёсика мыши."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<MouseWheel>', self._on_wheel)
        self.bind('<Button-4>', lambda e: self._step(+1))
        self.bind('<Button-5>', lambda e: self._step(-1))

    def _on_wheel(self, event):
        if event.delta > 0:
            self._step(+1)
        else:
            self._step(-1)
        return 'break'

    def _step(self, delta):
        try:
            val = int(float(self.get()))
        except ValueError:
            val = 0
        from_ = int(float(self.cget('from')))
        to = int(float(self.cget('to')))
        val = max(from_, min(to, val + delta))
        self.delete(0, tk.END)
        self.insert(0, str(val))


class WriteOffWindow(tk.Toplevel):
    def __init__(self, master, db, product_id, refresh_callback):
        super().__init__(master)
        self.db = db
        self.product_id = product_id
        self.refresh_callback = refresh_callback

        product = db.get_product_by_id(product_id)
        if not product:
            messagebox.showerror("Ошибка", "Товар не найден.", parent=master)
            self.destroy()
            return

        purchase_date = product[7] if len(product) > 7 else ''
        if purchase_date is None:
            purchase_date = ''

        self.title("Списание товара")
        self.geometry("420x380")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        info_frame = tk.LabelFrame(self, text="Информация о товаре", padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        fields = [
            ("ID:", product[0]),
            ("Код:", product[2]),
            ("Наименование:", product[1]),
            ("Цена закупки:", f"{product[3]:.2f}"),
            ("Цена продажи:", f"{product[4]:.2f}"),
            ("На складе:", product[5]),
            ("Дата закупки:", format_date(purchase_date) if purchase_date else "—"),
        ]
        for label, value in fields:
            row = tk.Frame(info_frame)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=16, anchor='w').pack(side=tk.LEFT)
            entry = tk.Entry(row, state='readonly')
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entry.config(state='normal')
            entry.insert(0, str(value))
            entry.config(state='readonly')

        qty_frame = tk.Frame(self)
        qty_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(qty_frame, text="Количество для списания:").pack(side=tk.LEFT)
        self.qty_var = tk.IntVar(value=0)
        self.qty_spin = WheelSpinbox(
            qty_frame, from_=0, to=product[5], textvariable=self.qty_var, width=8
        )
        self.qty_spin.pack(side=tk.LEFT, padx=10)
        bind_entry_shortcuts(self.qty_spin)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Списать", command=self.do_write_off).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)

        center_window(self)
        self.after(50, lambda: self.qty_spin.focus_set())

    def do_write_off(self):
        try:
            amount = int(self.qty_var.get())
        except ValueError:
            messagebox.showwarning("Внимание", "Введите корректное количество.", parent=self)
            return
        if amount <= 0:
            messagebox.showwarning("Внимание", "Укажите количество больше 0.", parent=self)
            return
        try:
            check_id = self.db.write_off_product(self.product_id, amount)
        except ValueError as e:
            messagebox.showwarning("Внимание", str(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось списать товар: {e}", parent=self)
            return
        messagebox.showinfo("Успех", f"Товар списан. Чек №{check_id}.", parent=self)
        self.refresh_callback(self.product_id)
        self.destroy()
