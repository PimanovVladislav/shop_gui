import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
from utils import SortableTreeview, SearchPanel, center_window
from database_operation import Database
from receipt_window import ReceiptWindow


class ChecksWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Просмотр чеков (возврат)")
        self.geometry("1200x550")
        self.state('zoomed')
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        style = ttk.Style(self)
        style.configure("Treeview.Heading",
                        font=('TkDefaultFont', 9, 'bold'), padding=(5, 8))

        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.search_panel = SearchPanel(main_frame, self.on_search)
        self.search_panel.pack(fill=tk.X, padx=5, pady=5)
        self.search_panel.bind_shortcuts(self)

        left_panel = tk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.checks_tree = SortableTreeview(
            left_panel,
            columns=('id', 'date', 'status', 'payment_type',
                     'sum', 'payed_sum', 'refused_sum'),
            show='headings',
            checkbox_column=False
        )
        col_widths = {'id': 50, 'date': 130, 'status': 120,
                      'payment_type': 100, 'sum': 80,
                      'payed_sum': 80, 'refused_sum': 80}
        headers = [('id', 'ID'), ('date', 'Дата'),
                   ('status', 'Статус'), ('payment_type', 'Тип оплаты'),
                   ('sum', 'Сумма'), ('payed_sum', 'Внесено'),
                   ('refused_sum', 'Возвращено')]
        for col, colname in headers:
            self.checks_tree.heading(col, text=colname)
            self.checks_tree.column(col, width=col_widths[col],
                                    anchor=tk.CENTER)
        self.checks_tree.setup_sorting()
        self.checks_tree.bind('<<TreeviewSelect>>', self.on_check_selected)
        self.checks_tree.pack(fill=tk.BOTH, expand=True)

        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cols = ('check', 'name', 'code', 'amount', 'price', 'total_price')
        self.products_tree = SortableTreeview(
            right_panel,
            columns=cols,
            show='headings',
            checkbox_column=True,
            double_click_check=False
        )
        self.products_tree.heading('check', text='☐')
        self.products_tree.heading('name', text='Название')
        self.products_tree.heading('code', text='Код')
        self.products_tree.heading('amount', text='Количество')
        self.products_tree.heading('price', text='Цена')
        self.products_tree.heading('total_price', text='Стоимость')

        self.products_tree.column('check', width=30, stretch=False)
        self.products_tree.column('name', width=180)
        self.products_tree.column('code', width=60)
        self.products_tree.column('amount', width=70, anchor=tk.CENTER)
        self.products_tree.column('price', width=80, anchor=tk.E)
        self.products_tree.column('total_price', width=80, anchor=tk.E)
        self.products_tree.setup_sorting()
        self.products_tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(right_panel)
        btn_frame.pack(fill=tk.X, pady=5)

        self.btn_return_selected = tk.Button(
            btn_frame, text="Возврат выбранных",
            command=self.return_selected_products)
        self.btn_return_selected.pack(side=tk.LEFT, padx=5)

        self.btn_return_all = tk.Button(
            btn_frame, text="Возврат всего чека",
            command=self.return_entire_check)
        self.btn_return_all.pack(side=tk.LEFT, padx=5)

        self.btn_open_receipt = tk.Button(
            btn_frame, text="Открыть чек",
            command=self.open_receipt)
        self.btn_open_receipt.pack(side=tk.LEFT, padx=5)

        self.current_check_id = None
        self.all_checks = []

        self.products_tree.bind('<Double-1>', self.on_product_double_click)
        self.products_tree.tag_configure('selected', background='#d3d3d3')

        self.refresh_checks()
        center_window(self)

    def _status_map(self):
        return {0: 'Ожидание оплаты', 1: 'Покупка', 2: 'Возврат', 3: 'Списание'}

    def refresh_checks(self):
        self.all_checks = self.db.get_all_checks()
        self._display_checks(self.all_checks)
        self.products_tree.delete(*self.products_tree.get_children())

    def _check_row_values(self, r):
        status_map = self._status_map()
        return (
            r[0], r[1], status_map.get(r[2], 'Неизвестно'),
            r[3], f"{r[4]:.2f}", f"{r[5]:.2f}", f"{r[6]:.2f}"
        )

    def _display_checks(self, rows):
        display = [(None, self._check_row_values(r)) for r in rows]
        self.checks_tree.load_rows(
            display,
            iid_fn=lambda row: None,
            values_fn=lambda row: row[1],
            restore_checked=False,
        )

    def on_check_selected(self, event):
        selected = self.checks_tree.selection()
        if not selected:
            return
        self.current_check_id = self.checks_tree.item(selected[0])['values'][0]
        status = self.checks_tree.item(selected[0])['values'][2]
        is_sale = status == 'Покупка'
        self.btn_return_selected.config(state='normal' if is_sale else 'disabled')
        self.btn_return_all.config(state='normal' if is_sale else 'disabled')
        self.refresh_products(self.current_check_id)

    def refresh_products(self, check_id):
        c = self.db.conn.cursor()
        c.execute(
            "SELECT cp.id, p.name, p.code, cp.amount, p.sale_price "
            "FROM check_products cp "
            "JOIN products p ON cp.product_id = p.id "
            "WHERE cp.id_check = ?",
            (check_id,)
        )
        rows = c.fetchall()
        display = []
        for r in rows:
            cp_id, name, code, amount, price = r
            total_price = price * amount
            display.append((
                str(cp_id),
                (name, code, amount, f"{price:.2f}", f"{total_price:.2f}")
            ))
        self.products_tree.load_rows(
            display,
            iid_fn=lambda row: row[0],
            values_fn=lambda row: row[1],
        )

    def on_product_double_click(self, event):
        region = self.products_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        rowid = self.products_tree.identify_row(event.y)
        column = self.products_tree.identify_column(event.x)
        if not rowid or not column:
            return
        col_num = int(column.replace('#', ''))
        if col_num == 4:
            current_vals = self.products_tree.item(rowid, 'values')
            current_amount = current_vals[3]
            new_amount = simpledialog.askinteger(
                "Изменить количество",
                f"Введите количество для возврата (макс {current_amount}):",
                minvalue=0, maxvalue=int(current_amount), parent=self
            )
            if new_amount is None:
                return
            price = float(current_vals[4])
            total_price = price * new_amount
            new_vals = list(current_vals)
            new_vals[3] = new_amount
            new_vals[5] = f"{total_price:.2f}"
            self.products_tree.item(rowid, values=new_vals)

    def open_receipt(self):
        if not self.current_check_id:
            messagebox.showwarning("Внимание", "Выберите чек.", parent=self)
            return
        row = self.db.get_receipt_text(self.current_check_id)
        if row is None:
            messagebox.showwarning("Внимание", "Текст чека не найден.", parent=self)
            return
        date_str, receipt_text = row
        if not receipt_text:
            messagebox.showwarning("Внимание", "Текст чека не найден.", parent=self)
            return
        ReceiptWindow(self, self.current_check_id, date_str, receipt_text)

    def return_selected_products(self):
        if not self.current_check_id:
            messagebox.showwarning("Внимание", "Выберите чек.", parent=self)
            return
        checked = self.products_tree.get_checked_iids()
        if not checked:
            messagebox.showwarning("Внимание",
                                   "Отметьте товары для возврата (колонка ☐).",
                                   parent=self)
            return
        c = self.db.conn.cursor()
        c.execute("SELECT payment_type FROM checks WHERE id = ?",
                  (self.current_check_id,))
        row = c.fetchone()
        if not row:
            messagebox.showerror("Ошибка", "Чек не найден.", parent=self)
            return
        payment_type = row[0]
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute(
            "INSERT INTO checks (date, status, payment_type, sum, payed_sum, refused_sum) "
            "VALUES (?, ?, ?, 0, 0, 0)",
            (now_str, 2, payment_type))
        new_check_id = c.lastrowid
        total_refund_sum = 0
        store_deltas = {}
        for cp_id in checked:
            vals = self.products_tree.item(cp_id, 'values')
            amount_to_return = int(vals[3])
            if amount_to_return <= 0:
                continue
            c.execute(
                "SELECT product_id FROM check_products WHERE id = ?", (cp_id,))
            product_row = c.fetchone()
            if not product_row:
                continue
            product_id = product_row[0]
            c.execute(
                "INSERT INTO check_products (id_check, product_id, amount) "
                "VALUES (?, ?, ?)",
                (new_check_id, product_id, amount_to_return))
            c.execute("SELECT amount FROM products WHERE id = ?", (product_id,))
            current_amount = c.fetchone()[0]
            c.execute("UPDATE products SET amount = ? WHERE id = ?",
                      (current_amount + amount_to_return, product_id))
            store_deltas[product_id] = store_deltas.get(product_id, 0) + amount_to_return
            price = float(vals[4])
            total_refund_sum += price * amount_to_return
        c.execute("UPDATE checks SET refused_sum = ?, sum = ? WHERE id = ?",
                  (total_refund_sum, -total_refund_sum, new_check_id))
        self.db.conn.commit()
        store = getattr(self.master, 'product_store', None)
        if store:
            store.apply_amount_deltas(store_deltas)
        messagebox.showinfo("Успех",
            f"Создан чек возврата №{new_check_id} на сумму {total_refund_sum:.2f}.",
            parent=self)
        self.refresh_checks()

    def return_entire_check(self):
        if not self.current_check_id:
            messagebox.showwarning("Внимание", "Выберите чек.", parent=self)
            return
        c = self.db.conn.cursor()
        c.execute("SELECT payment_type FROM checks WHERE id = ?",
                  (self.current_check_id,))
        row = c.fetchone()
        if not row:
            messagebox.showerror("Ошибка", "Чек не найден.", parent=self)
            return
        payment_type = row[0]
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute(
            "INSERT INTO checks (date, status, payment_type, sum, payed_sum, refused_sum) "
            "VALUES (?, ?, ?, 0, 0, 0)",
            (now_str, 2, payment_type))
        new_check_id = c.lastrowid
        total_refund_sum = 0
        store_deltas = {}
        c.execute("SELECT product_id, amount FROM check_products WHERE id_check = ?",
                  (self.current_check_id,))
        rows = c.fetchall()
        for product_id, amount in rows:
            if amount <= 0:
                continue
            c.execute(
                "INSERT INTO check_products (id_check, product_id, amount) "
                "VALUES (?, ?, ?)",
                (new_check_id, product_id, amount))
            c.execute("SELECT amount, sale_price FROM products WHERE id = ?",
                      (product_id,))
            current_amount, price = c.fetchone()
            c.execute("UPDATE products SET amount = ? WHERE id = ?",
                      (current_amount + amount, product_id))
            store_deltas[product_id] = store_deltas.get(product_id, 0) + amount
            total_refund_sum += price * amount
        c.execute("UPDATE checks SET refused_sum = ?, sum = ? WHERE id = ?",
                  (total_refund_sum, -total_refund_sum, new_check_id))
        self.db.conn.commit()
        store = getattr(self.master, 'product_store', None)
        if store:
            store.apply_amount_deltas(store_deltas)
        messagebox.showinfo("Успех",
            f"Создан чек возврата №{new_check_id} на сумму {total_refund_sum:.2f}.",
            parent=self)
        self.refresh_checks()

    def on_search(self, query):
        query = query.strip().lower()
        if not query:
            filtered = self.all_checks
        else:
            status_map = self._status_map()
            filtered = []
            for r in self.all_checks:
                id_str = str(r[0])
                date_str = (r[1] or '').lower()
                status_str = status_map.get(r[2], 'Неизвестно').lower()
                payment_str = (r[3] or '').lower()
                if (query in id_str or query in date_str or
                        query in status_str or query in payment_str):
                    filtered.append(r)
        self._display_checks(filtered)
        self.products_tree.delete(*self.products_tree.get_children())

    def on_close(self):
        if hasattr(self.master, "child_windows") and self in self.master.child_windows:
            self.master.child_windows.remove(self)
        self.destroy()
