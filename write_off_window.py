import tkinter as tk
from tkinter import messagebox
from resources.i18n import t
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
    def __init__(self, master, db, product_id, refresh_callback, store=None):
        super().__init__(master)
        self.db = db
        self.store = store or getattr(master, 'product_store', None)
        self.product_id = product_id
        self.refresh_callback = refresh_callback

        product = (self.store.get_db_row(product_id) if self.store
                   else db.get_product_by_id(product_id))
        if not product:
            messagebox.showerror(t('common.error'), t('write_off.product_not_found'),
                                 parent=master)
            self.destroy()
            return

        purchase_date = product[7] if len(product) > 7 else ''
        if purchase_date is None:
            purchase_date = ''
        supplier = product[8] if len(product) > 8 else ''
        if supplier is None:
            supplier = ''

        self.title(t('write_off.title'))
        self.geometry("420x380")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        info_frame = tk.LabelFrame(self, text=t('write_off.info_group'), padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        fields = [
            (t('warehouse.col.id') + ':', product[0]),
            (t('warehouse.col.code') + ':', product[2]),
            (t('warehouse.col.name') + ':', product[1]),
            (t('warehouse.col.buy_price') + ':', f"{product[3]:.2f}"),
            (t('warehouse.col.sale_price') + ':', f"{product[4]:.2f}"),
            (t('write_off.field.stock'), product[5]),
            (t('warehouse.col.purchase_date') + ':',
             format_date(purchase_date) if purchase_date else t('common.dash')),
            (t('write_off.field.supplier'),
             supplier if supplier else t('common.dash')),
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
        tk.Label(qty_frame, text=t('write_off.qty_label')).pack(side=tk.LEFT)
        self.qty_var = tk.IntVar(value=0)
        self.qty_spin = WheelSpinbox(
            qty_frame, from_=0, to=product[5], textvariable=self.qty_var, width=8
        )
        self.qty_spin.pack(side=tk.LEFT, padx=10)
        bind_entry_shortcuts(self.qty_spin)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text=t('write_off.btn.submit'),
                  command=self.do_write_off).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=t('common.cancel'),
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

        center_window(self)
        self.after(50, lambda: self.qty_spin.focus_set())

    def do_write_off(self):
        try:
            amount = int(self.qty_var.get())
        except ValueError:
            messagebox.showwarning(t('common.attention'), t('write_off.invalid_qty'),
                                   parent=self)
            return
        if amount <= 0:
            messagebox.showwarning(t('common.attention'), t('write_off.qty_zero'),
                                   parent=self)
            return
        try:
            check_id = self.db.write_off_product(self.product_id, amount)
        except ValueError as e:
            messagebox.showwarning(t('common.attention'), str(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror(t('common.error'), t('write_off.failed', error=e),
                                 parent=self)
            return
        if self.store:
            self.store.apply_amount_delta(self.product_id, -amount)
        messagebox.showinfo(t('common.success'), t('write_off.success', id=check_id),
                            parent=self)
        self.refresh_callback(self.product_id)
        self.destroy()
