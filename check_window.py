import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
from utils import SortableTreeview, SearchPanel
from database_operation import Database

class ChecksWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Просмотр чеков (возврат)")
        self.geometry("1200x520")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Настройка стиля для увеличения высоты шапки таблиц
        style = ttk.Style(self)
        style.configure("Treeview.Heading", font=('TkDefaultFont', 9, 'bold'), padding=(5,8))

        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.search_panel = SearchPanel(main_frame, self.on_search)
        self.search_panel.pack(fill=tk.X, padx=5, pady=5)

        # Таблица чеков слева
        self.checks_tree = SortableTreeview(main_frame, columns=('id', 'date', 'status', 'payment_type', 'sum', 'payed_sum', 'refused_sum'), show='headings')
        col_widths = {'id': 50, 'date': 50, 'status': 50, 'payment_type': 50, 'sum': 50, 'payed_sum': 50, 'refused_sum': 50}
        for col, colname in (('id', 'ID'), ('date','Дата'), ('status','Статус'), ('payment_type','Тип оплаты'), ('sum','Сумма'), ('payed_sum','Внесено'), ('refused_sum','Возвращено')):
            self.checks_tree.heading(col, text=colname)
            self.checks_tree.column(col, width=col_widths[col], anchor=tk.CENTER)
        self.checks_tree.setup_sorting()
        self.checks_tree.bind('<<TreeviewSelect>>', self.on_check_selected)
        self.checks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Таблица товаров без колонки чекбоксов
        cols = ('name', 'code', 'amount', 'price', 'total_price')
        self.products_tree = SortableTreeview(right_panel, columns=cols, show='headings')
        col_widths_products = {'name': 200, 'code': 50, 'amount': 50, 'price': 50, 'total_price': 50}
        self.products_tree.heading('name', text='Название')
        self.products_tree.column('name', width=col_widths_products['name'])
        self.products_tree.heading('code', text='Код')
        self.products_tree.column('code', width=col_widths_products['code'])
        self.products_tree.heading('amount', text='Количество')
        self.products_tree.column('amount', width=col_widths_products['amount'], anchor=tk.CENTER)
        self.products_tree.heading('price', text='Цена')
        self.products_tree.column('price', width=col_widths_products['price'], anchor=tk.E)
        self.products_tree.heading('total_price', text='Стоимость')
        self.products_tree.column('total_price', width=col_widths_products['total_price'], anchor=tk.E)
        self.products_tree.setup_sorting()
        self.products_tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(right_panel)
        btn_frame.pack(fill=tk.X, pady=5)

        self.btn_return_selected = tk.Button(btn_frame, text="Возврат выбранных товаров", command=self.return_selected_products)
        self.btn_return_selected.pack(side=tk.LEFT, padx=5)

        self.btn_return_all = tk.Button(btn_frame, text="Возврат всего чека", command=self.return_entire_check)
        self.btn_return_all.pack(side=tk.LEFT, padx=5)

        # Для хранения выделенных товаров (по цвету)
        self.selected_products = set()

        # Обработчики
        self.products_tree.bind('<Double-1>', self.on_product_double_click)

        self.on_search('')

    def refresh_checks(self):
        for i in self.checks_tree.get_children():
            self.checks_tree.delete(i)
        c = self.db.conn.cursor()
        c.execute('''
            SELECT checks.id, strftime('%d.%m.%Y %H:%M', checks.date), checks.status, payment_type.name, checks.sum, checks.payed_sum, checks.refused_sum
            FROM checks LEFT JOIN payment_type ON checks.payment_type = payment_type.id
            ORDER BY checks.date DESC
        ''')
        rows = c.fetchall()
        status_map = {0: 'Ожидание оплаты', 1: 'Покупка', 2: 'Возврат'}
        for r in rows:
            self.checks_tree.insert('', 'end', values=(
                r[0], r[1], status_map.get(r[2], 'Неизвестно'), r[3], f"{r[4]:.2f}", f"{r[5]:.2f}", f"{r[6]:.2f}"
            ))
        self.products_tree.delete(*self.products_tree.get_children())
        self.selected_products.clear()

    def on_check_selected(self, event):
        selected = self.checks_tree.selection()
        if not selected:
            return
        check_id = self.checks_tree.item(selected[0])['values'][0]
        self.refresh_products(check_id)

    def refresh_products(self, check_id):
        self.products_tree.delete(*self.products_tree.get_children())
        self.selected_products.clear()
        c = self.db.conn.cursor()
        c.execute('''
            SELECT cp.id, p.name, p.code, cp.amount, p.sale_price
            FROM check_products cp
            JOIN products p ON cp.product_id = p.id
            WHERE cp.id_check = ?
        ''', (check_id,))
        rows = c.fetchall()
        for r in rows:
            cp_id, name, code, amount, price = r
            total_price = price * amount
            self.products_tree.insert('', 'end', iid=str(cp_id), values=(name, code, amount, f"{price:.2f}", f"{total_price:.2f}"))

    def on_product_double_click(self, event):
        region = self.products_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        rowid = self.products_tree.identify_row(event.y)
        column = self.products_tree.identify_column(event.x)
        if not rowid or not column:
            return

        col_num = int(column.replace('#', ''))
        # Если клик по колонке "Количество" (3-я колонка)
        if col_num == 3:
            current_vals = self.products_tree.item(rowid, 'values')
            current_amount = current_vals[2]
            new_amount = simpledialog.askinteger("Изменить количество", f"Введите количество для возврата (макс {current_amount}):",
                                                 minvalue=0, maxvalue=int(current_amount), parent=self)
            if new_amount is None:
                return
            price = float(current_vals[3])
            total_price = price * new_amount
            new_vals = list(current_vals)
            new_vals[2] = new_amount
            new_vals[4] = f"{total_price:.2f}"
            self.products_tree.item(rowid, values=new_vals)

            # Клик по любой другой колонке - переключаем выделение (цвет)
        if rowid in self.selected_products:
            self.products_tree.item(rowid, tags=())
            self.selected_products.remove(rowid)
        else:
            self.products_tree.item(rowid, tags=('selected',))
            self.selected_products.add(rowid)

        # Обновляем стиль тегов
        self.products_tree.tag_configure('selected', background='#d3d3d3')  # светло-серый
        self.products_tree.selection_remove(self.products_tree.selection())

    def return_selected_products(self):
        selected_check = self.checks_tree.selection()
        if not selected_check:
            messagebox.showwarning("Внимание", "Выберите чек для возврата товаров.")
            return
        check_id = self.checks_tree.item(selected_check[0])['values'][0]

        if not self.selected_products:
            messagebox.showwarning("Внимание", "Выделите товары для возврата двойным кликом по строкам.")
            return

        c = self.db.conn.cursor()
        c.execute("SELECT payment_type FROM checks WHERE id = ?", (check_id,))
        row = c.fetchone()
        if not row:
            messagebox.showerror("Ошибка", "Исходный чек не найден.")
            return
        payment_type = row[0]

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO checks (date, status, payment_type, sum, payed_sum, refused_sum) VALUES (?, ?, ?, 0, 0, 0)",
                  (now_str, 2, payment_type))
        new_check_id = c.lastrowid

        total_refund_sum = 0

        for cp_id in self.selected_products:
            vals = self.products_tree.item(cp_id, 'values')
            amount_to_return = int(vals[2])
            if amount_to_return <= 0:
                continue

            c.execute("SELECT product_id FROM check_products WHERE id = ?", (cp_id,))
            product_row = c.fetchone()
            if not product_row:
                continue
            product_id = product_row[0]

            c.execute("INSERT INTO check_products (id_check, product_id, amount) VALUES (?, ?, ?)",
                      (new_check_id, product_id, amount_to_return))

            c.execute("SELECT amount FROM products WHERE id = ?", (product_id,))
            current_amount = c.fetchone()[0]
            c.execute("UPDATE products SET amount = ? WHERE id = ?", (current_amount + amount_to_return, product_id))

            price = float(vals[3])
            total_refund_sum += price * amount_to_return

        c.execute("UPDATE checks SET refused_sum = ?, sum = ? WHERE id = ?", (total_refund_sum, -total_refund_sum, new_check_id))

        self.db.conn.commit()

        messagebox.showinfo("Успех", f"Создан чек возврата №{new_check_id} с суммой возврата {total_refund_sum:.2f}.")

        self.refresh_checks()
        self.products_tree.delete(*self.products_tree.get_children())
        self.selected_products.clear()

    def return_entire_check(self):
        selected_check = self.checks_tree.selection()
        if not selected_check:
            messagebox.showwarning("Внимание", "Выберите чек для возврата.")
            return
        check_id = self.checks_tree.item(selected_check[0])['values'][0]

        c = self.db.conn.cursor()
        c.execute("SELECT payment_type FROM checks WHERE id = ?", (check_id,))
        row = c.fetchone()
        if not row:
            messagebox.showerror("Ошибка", "Исходный чек не найден.")
            return
        payment_type = row[0]

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO checks (date, status, payment_type, sum, payed_sum, refused_sum) VALUES (?, ?, ?, 0, 0, 0)",
                  (now_str, 2, payment_type))
        new_check_id = c.lastrowid

        total_refund_sum = 0

        c.execute("SELECT product_id, amount FROM check_products WHERE id_check = ?", (check_id,))
        rows = c.fetchall()

        for product_id, amount in rows:
            if amount <= 0:
                continue

            c.execute("INSERT INTO check_products (id_check, product_id, amount) VALUES (?, ?, ?)",
                      (new_check_id, product_id, amount))

            c.execute("SELECT amount, sale_price FROM products WHERE id = ?", (product_id,))
            current_amount, price = c.fetchone()
            c.execute("UPDATE products SET amount = ? WHERE id = ?", (current_amount + amount, product_id))

            total_refund_sum += price * amount

        c.execute("UPDATE checks SET refused_sum = ?, sum = ? WHERE id = ?", (total_refund_sum, -total_refund_sum, new_check_id))

        self.db.conn.commit()

        messagebox.showinfo("Успех", f"Создан чек возврата №{new_check_id} на весь чек с суммой возврата {total_refund_sum:.2f}.")

        self.refresh_checks()
        self.products_tree.delete(*self.products_tree.get_children())
        self.selected_products.clear()

    def on_search(self, query):
        query = query.strip().lower()
        # Сначала очистим таблицу
        self.checks_tree.delete(*self.checks_tree.get_children())
        c = self.db.conn.cursor()
        c.execute('''
            SELECT checks.id, strftime('%d.%m.%Y %H:%M', checks.date), checks.status, payment_type.name, checks.sum, checks.payed_sum, checks.refused_sum
            FROM checks LEFT JOIN payment_type ON checks.payment_type = payment_type.id
            ORDER BY checks.date DESC
        ''')
        rows = c.fetchall()
        status_map = {0: 'Ожидание оплаты', 1: 'Покупка', 2: 'Возврат'}
        for r in rows:
            id_str = str(r[0])
            date_str = r[1].lower()
            status_str = status_map.get(r[2], 'Неизвестно').lower()
            payment_str = (r[3] or '').lower()
            # Фильтр по нескольким полям
            if (query in id_str.lower() or
                    query in date_str or
                    query in status_str or
                    query in payment_str):
                self.checks_tree.insert('', 'end', values=(
                    r[0], r[1], status_map.get(r[2], 'Неизвестно'), r[3], f"{r[4]:.2f}", f"{r[5]:.2f}", f"{r[6]:.2f}"
                ))
        # Очистим правую таблицу и выделение
        self.products_tree.delete(*self.products_tree.get_children())
        self.selected_products.clear()

    def on_close(self):
        self.master.child_windows.remove(self)
        self.destroy()
