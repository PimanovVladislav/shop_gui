import tkinter as tk
from tkinter import messagebox
from payment_window import PaymentWindow
from utils import SortableTreeview, SearchPanel, bind_entry_shortcuts, center_window


class CashRegisterWindow(tk.Toplevel):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.store = master.product_store
        self.title("Касса")
        self.geometry("1100x550")
        self.state('zoomed')
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.all_products = []
        self.cart = []
        self._current_query = ''

        main_frame = tk.Frame(self)
        main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.search_panel = SearchPanel(main_frame, self.on_search)
        self.search_panel.pack(fill=tk.X, padx=5, pady=5)
        self.search_panel.bind_shortcuts(self)

        self.products_tree = SortableTreeview(
            main_frame,
            columns=('code', 'name', 'price', 'amount'),
            show='headings',
            checkbox_column=False,
            double_click_check=False
        )
        self.products_tree.heading('code', text='Код')
        self.products_tree.heading('name', text='Наименование')
        self.products_tree.heading('price', text='Цена продажи')
        self.products_tree.heading('amount', text='На складе')
        self.products_tree.column('code', width=60)
        self.products_tree.column('name', width=240)
        self.products_tree.column('price', width=90)
        self.products_tree.column('amount', width=90)
        self.products_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.products_tree.setup_sorting()
        self.products_tree.bind('<Double-1>', self._on_product_double_click)
        self.products_tree.bind('<Return>', self._on_products_enter)

        qty_frame = tk.Frame(main_frame)
        qty_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(qty_frame, text="Количество:").pack(side=tk.LEFT)
        self.qty_var = tk.IntVar(value=1)
        self.qty_spinbox = tk.Spinbox(qty_frame, from_=1, to=1000,
                                      textvariable=self.qty_var, width=6)
        self.qty_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        bind_entry_shortcuts(self.qty_spinbox)
        self.btn_add = tk.Button(qty_frame, text="Добавить в корзину (Enter)",
                                 takefocus=0, command=self.add_to_cart)
        self.btn_add.pack(side=tk.LEFT)

        right_frame = tk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 5))

        tk.Label(right_frame, text="Корзина", font=("Arial", 12, "bold")).pack()

        self.cart_tree = SortableTreeview(
            right_frame,
            columns=('check', 'name', 'price', 'amount', 'sum'),
            show='headings',
            checkbox_column=True,
        )
        self.cart_tree.heading('check', text='☐')
        self.cart_tree.heading('name', text='Наименование')
        self.cart_tree.heading('price', text='Цена')
        self.cart_tree.heading('amount', text='Кол-во')
        self.cart_tree.heading('sum', text='Сумма')
        self.cart_tree.column('check', width=30, stretch=False)
        self.cart_tree.column('name', width=200)
        self.cart_tree.column('price', width=80)
        self.cart_tree.column('amount', width=70)
        self.cart_tree.column('sum', width=90)
        self.cart_tree.pack(fill=tk.BOTH, expand=True)
        self.cart_tree.setup_sorting()
        self.cart_tree.bind('<Double-1>', self.on_cart_double_click)
        self.cart_tree.bind('<BackSpace>', self._on_cart_backspace)
        self.cart_tree.bind('<MouseWheel>', self._on_cart_wheel, add='+')
        self.editing_entry = None

        btn_cart = tk.Frame(right_frame)
        btn_cart.pack(fill=tk.X, pady=5)
        self.btn_decrease = tk.Button(btn_cart, text="−", width=3, takefocus=0,
                                      command=self.decrease_cart_qty)
        self.btn_decrease.pack(side=tk.LEFT, padx=2)
        self.btn_increase = tk.Button(btn_cart, text="+", width=3, takefocus=0,
                                      command=self.increase_cart_qty)
        self.btn_increase.pack(side=tk.LEFT, padx=2)
        self.btn_remove = tk.Button(btn_cart, text="Удалить", takefocus=0,
                                    command=self.remove_from_cart)
        self.btn_remove.pack(side=tk.LEFT, padx=2)

        self.btn_checkout = tk.Button(right_frame, text="Оформить продажу",
                                      command=self.checkout,
                                      bg="#4CAF50", fg="white",
                                      font=("Arial", 11, "bold"))
        self.btn_checkout.pack(pady=10, fill=tk.X)

        self.total_var = tk.StringVar(value="Итого: 0.00")
        tk.Label(right_frame, textvariable=self.total_var,
                 font=("Arial", 14)).pack()

        center_window(self)
        self.refresh_products()

    def refresh_products(self, product_ids=None):
        if product_ids:
            self._update_product_rows(product_ids)
            return
        self.all_products = self.store.get_available()
        self._display_products(self._filtered_products(self._current_query))
        self.search_panel.clear()

    def _filtered_products(self, query):
        query = query.lower()
        if not query:
            return self.all_products
        search_col = self.products_tree.get_search_column()
        mapping = {'code': 1, 'name': 2, 'price': 4, 'amount': 5}
        if search_col is not None and search_col in mapping:
            src_index = mapping[search_col]
            return [p for p in self.all_products
                    if src_index < len(p) and query in str(p[src_index]).lower()]
        return [p for p in self.all_products
                if any(query in str(f).lower() for f in (p[1], p[2], p[4], p[5]))]

    def _display_products(self, products):
        rows = [(str(p[0]), (p[1], p[2], p[4], p[5])) for p in products]
        self.products_tree.load_rows(
            rows,
            iid_fn=lambda row: row[0],
            values_fn=lambda row: row[1],
            restore_checked=False,
        )

    def _update_product_rows(self, product_ids):
        visible = {str(p[0]) for p in self._filtered_products(self._current_query)}
        for product_id in product_ids:
            p = self.store.get(product_id)
            iid = str(product_id)
            found = False
            for i, row in enumerate(self.all_products):
                if row[0] == product_id:
                    found = True
                    if p:
                        self.all_products[i] = p
                    else:
                        self.all_products.pop(i)
                    break
            if not found and p and p[5] > 0:
                self.all_products.append(p)

            if p is None or p[5] <= 0:
                if self.products_tree.exists(iid):
                    self.products_tree.delete(iid)
            elif iid in visible:
                if self.products_tree.exists(iid):
                    self.products_tree.item(
                        iid, values=(p[1], p[2], p[4], p[5]))
                else:
                    self.products_tree.insert(
                        '', 'end', iid=iid, values=(p[1], p[2], p[4], p[5]))

    def on_search(self, query):
        self._current_query = query
        self._display_products(self._filtered_products(query))

    def _get_product(self, product_id):
        return self.store.get_db_row(product_id)

    def _on_products_enter(self, event):
        self.add_to_cart()
        return 'break'

    def _on_cart_backspace(self, event):
        self.remove_from_cart()
        return 'break'

    def _on_cart_wheel(self, event):
        idx = self._selected_cart_index()
        if idx < 0:
            return
        if event.delta > 0:
            self._apply_cart_qty_delta(idx, +1)
        else:
            self._apply_cart_qty_delta(idx, -1)
        return 'break'

    def _apply_cart_qty_delta(self, idx, delta):
        if idx < 0 or idx >= len(self.cart):
            return
        product_id, name, price, old_qty = self.cart[idx]
        new_qty = old_qty + delta
        if new_qty <= 0:
            return
        product = self._get_product(product_id)
        if product and new_qty > product[5]:
            return
        self.cart[idx] = (product_id, name, price, new_qty)
        self._update_cart_row(product_id)
        self._restore_cart_focus(product_id)

    def _on_product_double_click(self, event):
        region = self.products_tree.identify("region", event.x, event.y)
        if region not in ("cell", "tree"):
            return
        rowid = self.products_tree.identify_row(event.y)
        if not rowid:
            return
        try:
            product_id = int(rowid)
        except ValueError:
            return
        product = self._get_product(product_id)
        if product is None:
            return
        qty = 1
        if product[5] <= 0:
            messagebox.showwarning("Внимание", "Товар закончился на складе.", parent=self)
            return
        for idx, item in enumerate(self.cart):
            if item[0] == product_id:
                new_amount = item[3] + qty
                if new_amount > product[5]:
                    messagebox.showwarning("Внимание",
                        f"Недостаточно на складе. Доступно: {product[5]}", parent=self)
                    return
                self.cart[idx] = (product_id, product[1], product[4], new_amount)
                self._update_cart_row(product_id)
                return
        self.cart.append((product_id, product[1], product[4], qty))
        self._insert_cart_row(product_id, product[1], product[4], qty)

    def add_to_cart(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для добавления.", parent=self)
            return
        product_id = int(selected[0])
        product = self._get_product(product_id)
        if product is None:
            messagebox.showerror("Ошибка", "Товар не найден.", parent=self)
            return
        qty = self.qty_var.get()
        if qty <= 0:
            messagebox.showwarning("Внимание", "Количество должно быть положительным.", parent=self)
            return
        if qty > product[5]:
            messagebox.showwarning("Внимание",
                f"Недостаточно на складе. Доступно: {product[5]}", parent=self)
            return
        for idx, item in enumerate(self.cart):
            if item[0] == product_id:
                new_amount = item[3] + qty
                if new_amount > product[5]:
                    messagebox.showwarning("Внимание",
                        f"Недостаточно на складе. Доступно: {product[5]}", parent=self)
                    return
                self.cart[idx] = (product_id, product[1], product[4], new_amount)
                self._update_cart_row(product_id)
                self._restore_products_focus(product_id)
                return
        self.cart.append((product_id, product[1], product[4], qty))
        self._insert_cart_row(product_id, product[1], product[4], qty)
        self._restore_products_focus(product_id)

    def _update_cart_total(self):
        total = sum(item[2] * item[3] for item in self.cart)
        self.total_var.set(f"Итого: {total:.2f}")

    def _insert_cart_row(self, product_id, name, price, qty):
        iid = str(product_id)
        sum_ = price * qty
        self.cart_tree.insert(
            '', 'end', iid=iid,
            values=(name, f"{price:.2f}", qty, f"{sum_:.2f}")
        )
        self._update_cart_total()

    def _update_cart_row(self, product_id):
        idx = next(i for i, item in enumerate(self.cart) if item[0] == product_id)
        _, name, price, qty = self.cart[idx]
        iid = str(product_id)
        sum_ = price * qty
        if self.cart_tree.exists(iid):
            self.cart_tree.set(iid, 'amount', qty)
            self.cart_tree.set(iid, 'sum', f'{sum_:.2f}')
        else:
            self._insert_cart_row(product_id, name, price, qty)
            return
        self._update_cart_total()

    def _remove_cart_rows(self, product_ids):
        for product_id in product_ids:
            iid = str(product_id)
            if self.cart_tree.exists(iid):
                self.cart_tree.delete(iid)
                self.cart_tree._checked_items.discard(iid)
        self._update_cart_total()

    def refresh_cart(self):
        checked = set(self.cart_tree.get_checked_iids())
        rows = []
        for item in self.cart:
            sum_ = item[2] * item[3]
            rows.append((
                str(item[0]),
                (item[1], f"{item[2]:.2f}", item[3], f"{sum_:.2f}")
            ))
        self.cart_tree.load_rows(
            rows,
            iid_fn=lambda row: row[0],
            values_fn=lambda row: row[1],
        )
        for iid in checked:
            if self.cart_tree.exists(iid):
                self.cart_tree._checked_items.add(iid)
                vals = list(self.cart_tree.item(iid, 'values'))
                if vals:
                    vals[0] = '\u2611'
                    self.cart_tree.item(iid, values=vals)
                    self.cart_tree._update_row_tags(iid)
        self.cart_tree.move_checked_to_top()
        self._update_cart_total()

    def _restore_products_focus(self, product_id):
        iid = str(product_id)
        if self.products_tree.exists(iid):
            self.products_tree.set_active(iid)
            self.products_tree.selection_set([iid])
        try:
            self.products_tree.tree.focus_set()
        except Exception:
            pass

    def _restore_cart_focus(self, product_id):
        iid = str(product_id)
        if self.cart_tree.exists(iid):
            self.cart_tree.set_active(iid)
            self.cart_tree.selection_set([iid])
        try:
            self.cart_tree.tree.focus_set()
        except Exception:
            pass

    def _selected_cart_index(self):
        checked = self.cart_tree.get_checked_iids()
        if len(checked) == 1:
            iid = checked[0]
            if self.cart_tree.exists(iid):
                return self.cart_tree.index(iid)
        iid = self.cart_tree.get_active_iid()
        if iid and self.cart_tree.exists(iid):
            return self.cart_tree.index(iid)
        sel = self.cart_tree.selection()
        if sel:
            return self.cart_tree.index(sel[0])
        focus_iid = self.cart_tree.focus()
        if focus_iid and self.cart_tree.exists(focus_iid):
            return self.cart_tree.index(focus_iid)
        return -1

    def decrease_cart_qty(self):
        self._modify_cart_qty(-1)

    def increase_cart_qty(self):
        self._modify_cart_qty(+1)

    def _modify_cart_qty(self, delta):
        idx = self._selected_cart_index()
        if idx < 0:
            messagebox.showwarning("Внимание", "Выберите товар в корзине.", parent=self)
            return
        product_id, name, price, old_qty = self.cart[idx]
        new_qty = old_qty + delta
        if new_qty <= 0:
            if messagebox.askyesno("Удаление",
                                   "Количество стало 0. Удалить товар из корзины?",
                                   parent=self):
                del self.cart[idx]
                self._remove_cart_rows([product_id])
            return
        product = self._get_product(product_id)
        if product and new_qty > product[5]:
            messagebox.showwarning("Внимание",
                f"Недостаточно на складе. Доступно: {product[5]}", parent=self)
            return
        self.cart[idx] = (product_id, name, price, new_qty)
        self._update_cart_row(product_id)
        self._restore_cart_focus(product_id)

    def remove_from_cart(self):
        checked = self.cart_tree.get_checked_iids()
        if checked:
            indices = sorted(
                [self.cart_tree.index(iid) for iid in checked
                 if self.cart_tree.exists(iid)],
                reverse=True
            )
            if not indices:
                messagebox.showwarning("Внимание", "Выберите товар в корзине.", parent=self)
                return
            removed_ids = []
            for idx in indices:
                if 0 <= idx < len(self.cart):
                    removed_ids.append(self.cart[idx][0])
                    del self.cart[idx]
            self._remove_cart_rows(removed_ids)
            return
        idx = self._selected_cart_index()
        if idx < 0:
            messagebox.showwarning("Внимание", "Выберите товар в корзине.", parent=self)
            return
        product_id = self.cart[idx][0]
        del self.cart[idx]
        self._remove_cart_rows([product_id])

    def on_cart_double_click(self, event):
        self.cart_tree.hide_cell_highlight()
        region = self.cart_tree.identify("region", event.x, event.y)
        if region != "cell":
            return False
        row_id = self.cart_tree.identify_row(event.y)
        column = self.cart_tree.identify_column(event.x)
        if column != '#4':
            return False
        if not row_id:
            return False

        x, y, width, height = self.cart_tree.bbox(row_id, column)
        value = self.cart_tree.set(row_id, 'amount')

        if self.editing_entry:
            self.editing_entry.destroy()

        self.editing_entry = tk.Entry(self.cart_tree.tree, width=5)
        self.editing_entry.place(x=x, y=y, width=width, height=height)
        self.editing_entry.insert(0, value)
        self.editing_entry.focus()

        def save_edit(event=None):
            new_val = self.editing_entry.get()
            try:
                new_qty = int(new_val)
                if new_qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Внимание",
                    "Количество должно быть положительным целым числом.", parent=self)
                self.editing_entry.focus()
                return
            idx = self.cart_tree.index(row_id)
            if idx < 0 or idx >= len(self.cart):
                self.editing_entry.destroy()
                self.editing_entry = None
                return
            product_id, name, price, old_qty = self.cart[idx]
            product = self._get_product(product_id)
            if not product:
                self.editing_entry.destroy()
                self.editing_entry = None
                return
            if new_qty > product[5]:
                messagebox.showwarning("Внимание",
                    f"Недостаточно на складе. Доступно: {product[5]}", parent=self)
                self.editing_entry.focus()
                return
            self.cart[idx] = (product_id, name, price, new_qty)
            self._update_cart_row(product_id)
            self.editing_entry.destroy()
            self.editing_entry = None

        self.editing_entry.bind('<Return>', save_edit)
        self.editing_entry.bind('<FocusOut>',
            lambda e: self.editing_entry and self.editing_entry.destroy())
        return True

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Внимание", "Корзина пуста.", parent=self)
            return
        pay_window = PaymentWindow(
            self, self.db, self.cart,
            self.refresh_products, self.clear_cart,
            store=self.store
        )
        pay_window.grab_set()

    def clear_cart(self):
        self.cart.clear()
        self.refresh_cart()

    def on_close(self):
        if hasattr(self.master, "child_windows") and self in self.master.child_windows:
            self.master.child_windows.remove(self)
        self.destroy()
