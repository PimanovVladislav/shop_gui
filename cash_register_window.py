import tkinter as tk
from tkinter import messagebox
from payment_window import PaymentWindow
from utils import SortableTreeview, SearchPanel, bind_entry_shortcuts


class CashRegisterWindow(tk.Toplevel):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.title("Касса")
        self.geometry("1100x550")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.all_products = []
        self.cart = []

        # ── Левая часть ───────────────────────────────
        main_frame = tk.Frame(self)
        main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.search_panel = SearchPanel(main_frame, self.on_search)
        self.search_panel.pack(fill=tk.X, padx=5, pady=5)

        # Таблица товаров: чекбоксы есть, НО двойной клик НЕ переключает чекбокс —
        # он добавляет товар в корзину (см. _on_product_double_click)
        self.products_tree = SortableTreeview(
            main_frame,
            columns=('check', 'code', 'name', 'price', 'amount'),
            show='headings',
            checkbox_column=True,
            double_click_check=False
        )
        self.products_tree.heading('check', text='☐')
        self.products_tree.heading('code', text='Код')
        self.products_tree.heading('name', text='Наименование')
        self.products_tree.heading('price', text='Цена продажи')
        self.products_tree.heading('amount', text='На складе')
        self.products_tree.column('check', width=30, stretch=False)
        self.products_tree.column('code', width=60)
        self.products_tree.column('name', width=200)
        self.products_tree.column('price', width=80)
        self.products_tree.column('amount', width=80)
        self.products_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.products_tree.setup_sorting()

        # Двойной клик по товару → добавить 1 шт. в корзину
        self.products_tree.bind('<Double-1>', self._on_product_double_click)

        # ── Правая часть: корзина ─────────────────────
        right_frame = tk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(right_frame, text="Корзина", font=("Arial", 12, "bold")).pack()

        # Корзина: двойной клик по ячейке «Кол-во» = редактирование,
        # поэтому двойной клик не переключает чекбокс
        self.cart_tree = SortableTreeview(
            right_frame,
            columns=('check', 'name', 'price', 'amount', 'sum'),
            show='headings',
            checkbox_column=True,
            double_click_check=False,
            height=12
        )
        self.cart_tree.heading('check', text='☐')
        self.cart_tree.heading('name', text='Наименование')
        self.cart_tree.heading('price', text='Цена')
        self.cart_tree.heading('amount', text='Кол-во')
        self.cart_tree.heading('sum', text='Сумма')
        self.cart_tree.column('check', width=30, stretch=False)
        self.cart_tree.column('name', width=180)
        self.cart_tree.column('price', width=70)
        self.cart_tree.column('amount', width=60)
        self.cart_tree.column('sum', width=80)
        self.cart_tree.pack(fill=tk.BOTH, expand=True)
        self.cart_tree.bind('<Double-1>', self.on_cart_double_click)
        self.editing_entry = None

        # Количество для добавления
        qty_frame = tk.Frame(right_frame)
        qty_frame.pack(pady=5)
        tk.Label(qty_frame, text="Количество:").pack(side=tk.LEFT)
        self.qty_var = tk.IntVar(value=1)
        self.qty_spinbox = tk.Spinbox(qty_frame, from_=1, to=100,
                                      textvariable=self.qty_var, width=5)
        self.qty_spinbox.pack(side=tk.LEFT)
        bind_entry_shortcuts(self.qty_spinbox)

        tk.Button(right_frame, text="Добавить в корзину",
                  command=self.add_to_cart).pack(pady=3)

        # Кнопки +/−
        qty_edit_frame = tk.Frame(right_frame)
        qty_edit_frame.pack(pady=3)
        tk.Label(qty_edit_frame, text="Изменить кол-во:").pack(
            side=tk.LEFT, padx=(0, 5))
        tk.Button(qty_edit_frame, text="−", width=2,
                  command=self.decrease_cart_qty).pack(side=tk.LEFT, padx=1)
        tk.Button(qty_edit_frame, text="+", width=2,
                  command=self.increase_cart_qty).pack(side=tk.LEFT, padx=1)

        tk.Button(right_frame, text="Оформить продажу", command=self.checkout,
                  bg="#4CAF50", fg="white",
                  font=("Arial", 11, "bold")).pack(pady=10)

        self.total_var = tk.StringVar(value="Итого: 0.00")
        tk.Label(right_frame, textvariable=self.total_var,
                 font=("Arial", 14)).pack()

        self.refresh_products()

    # ── Данные ───────────────────────────────────────
    def refresh_products(self):
        self.all_products = self.db.get_available_products()
        self.update_tree(self.all_products)
        self.search_panel.clear()

    def update_tree(self, products):
        self.products_tree.clear_checks()
        self.products_tree.delete(*self.products_tree.get_children())
        for p in products:
            self.products_tree.insert('', 'end', iid=str(p[0]),
                                      values=(p[1], p[2], p[4], p[5]))

    def on_search(self, query):
        query = query.lower()
        if not query:
            self.update_tree(self.all_products)
            return
        filtered = [p for p in self.all_products
                    if any(query in str(f).lower()
                           for f in (p[1], p[2], p[4], p[5]))]
        self.update_tree(filtered)

    # ── Двойной клик по товару → +1 в корзину ────────
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
        product = self.db.get_product_by_id(product_id)
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
                break
        else:
            self.cart.append((product_id, product[1], product[4], qty))
        self.refresh_cart()

    # ── Добавление в корзину (кнопка) ────────────────
    def add_to_cart(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для добавления.", parent=self)
            return
        product_id = int(selected[0])
        product = self.db.get_product_by_id(product_id)
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
                break
        else:
            self.cart.append((product_id, product[1], product[4], qty))
        self.refresh_cart()

    # ── Корзина ─────────────────────────────────────
    def refresh_cart(self):
        self.cart_tree.clear_checks()
        self.cart_tree.delete(*self.cart_tree.get_children())
        total = 0
        for item in self.cart:
            sum_ = item[2] * item[3]
            total += sum_
            self.cart_tree.insert('', 'end',
                values=(item[1], f"{item[2]:.2f}", item[3], f"{sum_:.2f}"))
        self.total_var.set(f"Итого: {total:.2f}")

    def decrease_cart_qty(self):
        self._modify_cart_qty(-1)

    def increase_cart_qty(self):
        self._modify_cart_qty(+1)

    def _modify_cart_qty(self, delta):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар в корзине.", parent=self)
            return
        idx = self.cart_tree.index(selected[0])
        if idx < 0 or idx >= len(self.cart):
            return
        product_id, name, price, old_qty = self.cart[idx]
        new_qty = old_qty + delta
        if new_qty <= 0:
            if messagebox.askyesno("Удаление",
                                   "Количество стало 0. Удалить товар из корзины?",
                                   parent=self):
                del self.cart[idx]
                self.refresh_cart()
            return
        product = self.db.get_product_by_id(product_id)
        if product and new_qty > product[5]:
            messagebox.showwarning("Внимание",
                f"Недостаточно на складе. Доступно: {product[5]}", parent=self)
            return
        self.cart[idx] = (product_id, name, price, new_qty)
        self.refresh_cart()
        children = self.cart_tree.get_children('')
        if idx < len(children):
            self.cart_tree.selection_set(children[idx])

    def on_cart_double_click(self, event):
        region = self.cart_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.cart_tree.identify_row(event.y)
        column = self.cart_tree.identify_column(event.x)
        if column != '#4':
            return
        if not row_id:
            return

        x, y, width, height = self.cart_tree.bbox(row_id, column)
        value = self.cart_tree.set(row_id, 'amount')

        if self.editing_entry:
            self.editing_entry.destroy()

        self.editing_entry = tk.Entry(self.cart_tree, width=5)
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
            product = self.db.get_product_by_id(product_id)
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
            self.refresh_cart()
            self.editing_entry.destroy()
            self.editing_entry = None

        self.editing_entry.bind('<Return>', save_edit)
        self.editing_entry.bind('<FocusOut>',
            lambda e: self.editing_entry and self.editing_entry.destroy())

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Внимание", "Корзина пуста.", parent=self)
            return
        pay_window = PaymentWindow(self, self.db, self.cart,
                                   self.refresh_products, self.clear_cart)
        pay_window.grab_set()

    def clear_cart(self):
        self.cart.clear()
        self.refresh_cart()

    def on_close(self):
        if hasattr(self.master, "child_windows") and self in self.master.child_windows:
            self.master.child_windows.remove(self)
        self.destroy()
