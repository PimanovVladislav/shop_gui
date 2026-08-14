import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from utils import bind_entry_shortcuts
from receipt_window import ReceiptWindow


class PaymentWindow(tk.Toplevel):
    def __init__(self, master, db, cart, refresh_products_callback, clear_cart_callback):
        super().__init__(master)
        self.db = db
        self.cart = cart
        self.refresh_products_callback = refresh_products_callback
        self.clear_cart_callback = clear_cart_callback

        self.title("Оплата")
        self.geometry("300x360")
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

        # Кнопка просмотра чека (становится активной после успешной оплаты)
        self.btn_view_receipt = tk.Button(
            self, text="Просмотр чека",
            command=self.view_receipt, state='disabled')
        self.btn_view_receipt.pack(pady=(0, 10))

        self._last_check_id = None
        self._last_date_str = None

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

    def _build_receipt_text(self, date_str, payment_type_id, total_sum, payed, refused):
        """Формирует текстовое представление чека."""
        lines = []
        lines.append("=" * 42)
        lines.append("МАГАЗИН РЫБОЛОВНЫХ ТОВАРОВ".center(42))
        lines.append("КАССОВЫЙ ЧЕК".center(42))
        lines.append("=" * 42)
        lines.append("Дата: {0}".format(date_str))
        lines.append("Тип оплаты: {0}".format(
            self._payment_type_name(payment_type_id)))
        lines.append("-" * 42)
        for item in self.cart:
            product_id, name, price, amount = item
            item_sum = price * amount
            lines.append("{0}".format(name))
            lines.append("  {0} x {1:.2f} = {2:.2f}".format(amount, price, item_sum))
        lines.append("-" * 42)
        lines.append("ИТОГО: {0:.2f}".format(total_sum))
        lines.append("Внесено: {0:.2f}".format(payed))
        lines.append("Сдача: {0:.2f}".format(refused))
        lines.append("=" * 42)
        lines.append("СПАСИБО ЗА ПОКУПКУ!".center(42))
        return "\n".join(lines)

    def _payment_type_name(self, payment_type_id):
        for pt in self.payment_types:
            if pt[0] == payment_type_id:
                return pt[1]
        return str(payment_type_id)

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

        # Сохраняем текст чека в БД
        receipt_text = self._build_receipt_text(
            date_str, self.payment_var.get(), self.total_sum, payed, refused)
        try:
            self.db.save_receipt_text(check_id, receipt_text)
        except Exception:
            pass

        self._last_check_id = check_id
        self._last_date_str = date_str

        self.btn_view_receipt.config(state='normal')
        self.btn_view_receipt.focus_set()

        messagebox.showinfo("Успех", "Оплата прошла успешно. Сдача: {0:.2f}".format(refused),
                            parent=self)
        self.refresh_products_callback()
        self.clear_cart_callback()

    def view_receipt(self):
        if self._last_check_id is None:
            messagebox.showwarning("Внимание", "Чек ещё не создан.", parent=self)
            return
        row = self.db.get_receipt_text(self._last_check_id)
        date_str = self._last_date_str
        receipt_text = ""
        if row is not None:
            date_str = row[0] or date_str
            receipt_text = row[1] or ""
        if not receipt_text:
            messagebox.showwarning("Внимание", "Текст чека не найден.", parent=self)
            return
        ReceiptWindow(self, self._last_check_id, date_str, receipt_text)

    def on_close(self):
        self.destroy()
