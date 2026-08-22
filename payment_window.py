import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from resources.receipt_templates import build_sale_receipt
from resources.i18n import t
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

        self.title(t('payment.title'))
        self.geometry("300x360")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._paid = False
        self._radio_buttons = []

        self.total_sum = sum(item[2]*item[3] for item in cart)
        tk.Label(self, text=t('payment.total', sum=f'{self.total_sum:.2f}'),
                 font=("Arial", 14)).pack(pady=10)

        tk.Label(self, text=t('payment.type_label')).pack()
        self.payment_types = self.db.get_payment_types()
        self.payment_var = tk.IntVar()
        self.payment_var.set(self.payment_types[0][0])
        for pt in self.payment_types:
            rb = tk.Radiobutton(self, text=pt[1], variable=self.payment_var,
                                value=pt[0])
            rb.pack(anchor='w')
            self._radio_buttons.append(rb)

        tk.Label(self, text=t('payment.payed_label')).pack()
        self.payed_var = tk.DoubleVar(value=self.total_sum)
        self.payed_entry = tk.Entry(self, textvariable=self.payed_var)
        self.payed_entry.pack()
        bind_entry_shortcuts(self.payed_entry)

        self.btn_pay = tk.Button(self, text=t('payment.btn.pay'), command=self.pay)
        self.btn_pay.pack(pady=20)

        self.btn_view_receipt = tk.Button(
            self, text=t('payment.btn.view_receipt'),
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
        return build_sale_receipt(
            self.cart,
            date_str,
            self._payment_type_name(payment_type_id),
            total_sum,
            payed,
            refused,
            format_datetime,
        )

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
            messagebox.showwarning(t('common.attention'), t('payment.too_small'),
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
            messagebox.showwarning(t('common.attention'), str(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror(t('common.error'), t('payment.failed', error=e), parent=self)
            return

        if self.store:
            self.store.apply_amount_deltas({pid: -amt for pid, amt in items})

        self._last_check_id = check_id
        self._last_date_str = date_str

        messagebox.showinfo(t('common.success'),
                            t('payment.success', change=f'{refused:.2f}'),
                            parent=self)
        self.refresh_products_callback([item[0] for item in self.cart])
        self.clear_cart_callback()
        self._lock_after_payment()

    def view_receipt(self):
        if self._last_check_id is None:
            messagebox.showwarning(t('common.attention'), t('payment.no_check'), parent=self)
            return
        row = self.db.get_receipt_text(self._last_check_id)
        date_str = self._last_date_str
        receipt_text = ""
        if row is not None:
            date_str = row[0] or date_str
            receipt_text = row[1] or ""
        if not receipt_text:
            messagebox.showwarning(t('common.attention'), t('payment.no_receipt_text'), parent=self)
            return
        ReceiptWindow(self, self._last_check_id, date_str, receipt_text)

    def on_close(self):
        self.grab_release()
        self.destroy()
