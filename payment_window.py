import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from utils import bind_entry_shortcuts


class PaymentWindow(tk.Toplevel):
    def __init__(self, master, db, cart, refresh_products_callback, clear_cart_callback):
        super().__init__(master)
        self.db = db
        self.cart = cart
        self.refresh_products_callback = refresh_products_callback
        self.clear_cart_callback = clear_cart_callback

        self.title("Оплата")
        self.geometry("300x300")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.total_sum = sum(item[2]*item[3] for item in cart)
        tk.Label(self, text="Сумма к оплате: {0:.2f}".format(self.total_sum),
                 font=("Arial", 14)).pack(pady=10)

        tk.Label(self, text="Тип оплаты:").pack()
        self.payment_types = self.db.get_payment_types()
        self.payment_var = tk.IntVar()
        self.payment_var.set(self.payment_types[0][0])
        for pt in self.payment_types:
            tk.Radiobutton(self, text=pt[1], variable=self.payment_var,
                           value=pt[0]).pack(anchor='w')

        tk.Label(self, text="Внесенная сумма:").pack()
        self.payed_var = tk.DoubleVar(value=self.total_sum)
        self.payed_entry = tk.Entry(self, textvariable=self.payed_var)
        self.payed_entry.pack()
        bind_entry_shortcuts(self.payed_entry)

        btn_pay = tk.Button(self, text="Оплатить", command=self.pay)
        btn_pay.pack(pady=20)

        self.after(50, self._focus_amount)

    def _focus_amount(self):
        try:
            self.payed_entry.focus_force()
            self.payed_entry.focus_set()
            self.payed_entry.select_range(0, tk.END)
        except Exception:
            pass
        try:
            self.lift()
        except Exception:
            pass

    def pay(self):
        payed = self.payed_var.get()
        if payed < self.total_sum:
            messagebox.showwarning("Внимание", "Внесенная сумма меньше суммы к оплате.",
                                   parent=self)
            self._focus_amount()
            return
        refused = payed - self.total_sum

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        check_id = self.db.create_check(date_str, 1, self.payment_var.get(),
                                        self.total_sum, payed, refused)

        for item in self.cart:
            product_id, name, price, amount = item
            self.db.add_product_to_check(product_id, amount, check_id)
            product = self.db.get_product_by_id(product_id)
            new_amount = product[5] - amount
            self.db.update_product_amount(product_id, new_amount)

        messagebox.showinfo("Успех", "Оплата прошла успешно. Сдача: {0:.2f}".format(refused),
                            parent=self)
        self.refresh_products_callback()
        self.clear_cart_callback()
        self.destroy()

    def on_close(self):
        self.destroy()
