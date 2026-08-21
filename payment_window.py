import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from utils import bind_entry_shortcuts, center_window, format_datetime
from receipt_window import ReceiptWindow


class PaymentWindow(tk.Toplevel):
    def __init__(self, master, db, cart, refresh_products_callback, clear_cart_callback,
                 store=None):
        super().__init__(master)
        self.db = db
        self.store = store or getattr(master, 'product_store', None)
        self.cart = cart
        self.refresh_products_callback = refresh_products_callback
        self.clear_cart_callback = clear_cart_callback

        self.title("Оплата")
        self.geometry("300x360")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._paid = False
        self._radio_buttons = []

        self.total_sum = sum(item[2]*item[3] for item in cart)
        tk.Label(self, text="Сумма к оплате: {0:.2f}".format(self.total_sum),
                 font=("Arial", 14)).pack(pady=10)

        tk.Label(self, text="Тип оплаты:").pack()
        self.payment_types = self.db.get_payment_types()
        self.payment_var = tk.IntVar()
        self.payment_var.set(self.payment_types[0][0])
        for pt in self.payment_types:
            rb = tk.Radiobutton(self, text=pt[1], variable=self.payment_var,
                                value=pt[0])
            rb.pack(anchor='w')
            self._radio_buttons.append(rb)

        tk.Label(self, text="Внесенная сумма:").pack()
        self.payed_var = tk.DoubleVar(value=self.total_sum)
        self.payed_entry = tk.Entry(self, textvariable=self.payed_var)
        self.payed_entry.pack()
        bind_entry_shortcuts(self.payed_entry)

        self.btn_pay = tk.Button(self, text="Оплатить", command=self.pay)
        self.btn_pay.pack(pady=20)

        self.btn_view_receipt = tk.Button(
            self, text="Просмотр чеков",
            command=self.view_receipt, state='disabled')
        self.btn_view_receipt.pack(pady=(0, 10))

        self._last_check_id = None
        self._last_date_str = None

        self.after(50, self._focus_amount)
        center_window(self)

    def _focus_amount(self):
        if self._paid:
            return
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

    def _lock_after_payment(self):
        """Блокирует повторную оплату; доступны только закрытие и просмотр чека."""
        self._paid = True
        self.btn_pay.config(state='disabled')
        self.payed_entry.config(state='disabled')
        for rb in self._radio_buttons:
            rb.config(state='disabled')
        self.btn_view_receipt.config(state='normal')
        self.btn_view_receipt.focus_set()

    def _build_receipt_text(self, date_str, payment_type_id, total_sum, payed, refused):
        lines = []
        lines.append("=" * 42)
        lines.append("МАГАЗИН РЫБОЛОВНЫХ ТОВАРОВ".center(42))
        lines.append("КАССОВЫЙ ЧЕК".center(42))
        lines.append("=" * 42)
        lines.append("Дата: {0}".format(format_datetime(date_str)))
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
        if self._paid:
            return
        payed = self.payed_var.get()
        if payed < self.total_sum:
            messagebox.showwarning("Внимание", "Внесенная сумма меньше суммы к оплате.",
                                   parent=self)
            self._focus_amount()
            return
        refused = payed - self.total_sum
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items = [(item[0], item[3]) for item in self.cart]
        receipt_text = self._build_receipt_text(
            date_str, self.payment_var.get(), self.total_sum, payed, refused)

        try:
            check_id = self.db.process_sale(
                date_str, 1, self.payment_var.get(),
                self.total_sum, payed, refused, items, receipt_text
            )
        except ValueError as e:
            messagebox.showwarning("Внимание", str(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось провести оплату: {e}", parent=self)
            return

        if self.store:
            self.store.apply_amount_deltas({pid: -amt for pid, amt in items})

        self._last_check_id = check_id
        self._last_date_str = date_str

        messagebox.showinfo("Успех", "Оплата прошла успешно. Сдача: {0:.2f}".format(refused),
                            parent=self)
        self.refresh_products_callback([item[0] for item in self.cart])
        self.clear_cart_callback()
        self._lock_after_payment()

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
        self.grab_release()
        self.destroy()
