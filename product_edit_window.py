import tkinter as tk
from tkinter import messagebox


class ProductEditWindow(tk.Toplevel):
    def __init__(self, master, db, refresh_callback, product=None):
        super().__init__(master)
        self.db = db
        self.refresh_callback = refresh_callback
        self.product = product

        self.title("Редактирование товара" if product else "Добавление товара")
        self.geometry("400x300")
        self.wm_iconbitmap("main_icon.ico")

        # Поля
        tk.Label(self, text="Наименование:").pack()
        self.name_var = tk.StringVar(value=product[1] if product else "")
        tk.Entry(self, textvariable=self.name_var).pack()

        tk.Label(self, text="Код товара:").pack()
        self.code_var = tk.StringVar(value=product[2] if product else "")
        tk.Entry(self, textvariable=self.code_var).pack()

        tk.Label(self, text="Цена закупки:").pack()
        self.buy_price_var = tk.DoubleVar(value=product[3] if product else 0.0)
        tk.Entry(self, textvariable=self.buy_price_var).pack()

        tk.Label(self, text="Цена продажи:").pack()
        self.sale_price_var = tk.DoubleVar(value=product[4] if product else 0.0)
        tk.Entry(self, textvariable=self.sale_price_var).pack()

        tk.Label(self, text="Количество:").pack()
        self.amount_var = tk.IntVar(value=product[5] if product else 0)
        tk.Entry(self, textvariable=self.amount_var).pack()

        btn_save = tk.Button(self, text="Сохранить", command=self.save)
        btn_save.pack(pady=10)

    def save(self):
        name = self.name_var.get().strip()
        code = self.code_var.get().strip()
        try:
            buy_price = float(self.buy_price_var.get())
            sale_price = float(self.sale_price_var.get())
            amount = int(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат числовых полей")
            return

        if not name:
            messagebox.showwarning("Внимание", "Наименование не может быть пустым")
            return
        if buy_price < 0 or sale_price < 0 or amount < 0:
            messagebox.showwarning("Внимание", "Числовые значения не могут быть отрицательными")
            return

        if self.product:
            # Обновляем товар
            c = self.db.conn.cursor()
            c.execute('''
                UPDATE products SET name=?, code=?, buy_price=?, sale_price=?, amount=?
                WHERE id=?
            ''', (name, code, buy_price, sale_price, amount, self.product[0]))
            self.db.conn.commit()
        else:
            # Добавляем новый товар
            self.db.add_product(name, code, buy_price, sale_price, amount)

        self.refresh_callback()
        self.destroy()