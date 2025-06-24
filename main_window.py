import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_NAME = 'fish_store.db'

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                code TEXT,
                buy_price REAL,
                sale_price REAL,
                amount INTEGER
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS payment_type (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                status INTEGER,
                payment_type INTEGER,
                sum REAL,
                payed_sum REAL,
                refused_sum REAL,
                FOREIGN KEY(payment_type) REFERENCES payment_type(id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS check_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                amount INTEGER,
                id_check INTEGER,
                FOREIGN KEY(product_id) REFERENCES products(id),
                FOREIGN KEY(id_check) REFERENCES checks(id)
            )
        ''')
        # Добавим базовые типы оплаты, если их нет
        c.execute("SELECT COUNT(*) FROM payment_type")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO payment_type (name) VALUES (?)", [('Наличные',), ('Карта',), ('Электронный кошелек',)])
        self.conn.commit()

    # Методы для работы с таблицей products
    def get_all_products(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM products")
        return c.fetchall()

    def add_product(self, name, code, buy_price, sale_price, amount):
        c = self.conn.cursor()
        c.execute("INSERT INTO products (name, code, buy_price, sale_price, amount) VALUES (?, ?, ?, ?, ?)",
                  (name, code, buy_price, sale_price, amount))
        self.conn.commit()

    def update_product_amount(self, product_id, new_amount):
        c = self.conn.cursor()
        c.execute("UPDATE products SET amount = ? WHERE id = ?", (new_amount, product_id))
        self.conn.commit()

    def get_product_by_id(self, product_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return c.fetchone()

    # Методы для работы с payment_type
    def get_payment_types(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM payment_type")
        return c.fetchall()

    # Методы для работы с чеками
    def create_check(self, date, status, payment_type, sum_, payed_sum, refused_sum):
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO checks (date, status, payment_type, sum, payed_sum, refused_sum)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, status, payment_type, sum_, payed_sum, refused_sum))
        self.conn.commit()
        return c.lastrowid

    def add_product_to_check(self, product_id, amount, id_check):
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO check_products (product_id, amount, id_check)
            VALUES (?, ?, ?)
        ''', (product_id, amount, id_check))
        self.conn.commit()

    def close(self):
        self.conn.close()


class CashRegisterWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Касса")
        self.geometry("600x400")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.products = self.db.get_all_products()
        self.cart = []  # список кортежей (product_id, name, sale_price, amount)

        # Список товаров
        self.products_tree = ttk.Treeview(self, columns=('id', 'name', 'price', 'amount'), show='headings')
        self.products_tree.heading('id', text='ID')
        self.products_tree.heading('name', text='Наименование')
        self.products_tree.heading('price', text='Цена продажи')
        self.products_tree.heading('amount', text='На складе')
        self.products_tree.column('id', width=30)
        self.products_tree.column('name', width=200)
        self.products_tree.column('price', width=80)
        self.products_tree.column('amount', width=80)
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.refresh_products()

        # Панель справа - корзина и управление
        right_frame = tk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        # Корзина
        tk.Label(right_frame, text="Корзина").pack()
        self.cart_tree = ttk.Treeview(right_frame, columns=('name', 'price', 'amount', 'sum'), show='headings')
        self.cart_tree.heading('name', text='Наименование')
        self.cart_tree.heading('price', text='Цена')
        self.cart_tree.heading('amount', text='Кол-во')
        self.cart_tree.heading('sum', text='Сумма')
        self.cart_tree.pack(fill=tk.BOTH, expand=True)

        # Кол-во для добавления
        qty_frame = tk.Frame(right_frame)
        qty_frame.pack(pady=5)
        tk.Label(qty_frame, text="Количество:").pack(side=tk.LEFT)
        self.qty_var = tk.IntVar(value=1)
        self.qty_spinbox = tk.Spinbox(qty_frame, from_=1, to=100, textvariable=self.qty_var, width=5)
        self.qty_spinbox.pack(side=tk.LEFT)

        # Кнопки
        btn_add = tk.Button(right_frame, text="Добавить в корзину", command=self.add_to_cart)
        btn_add.pack(pady=5)

        btn_remove = tk.Button(right_frame, text="Удалить из корзины", command=self.remove_from_cart)
        btn_remove.pack(pady=5)

        btn_pay = tk.Button(right_frame, text="Оформить продажу", command=self.checkout)
        btn_pay.pack(pady=20)

        # Итог
        self.total_var = tk.StringVar(value="Итого: 0.00")
        tk.Label(right_frame, textvariable=self.total_var, font=("Arial", 14)).pack()

    def refresh_products(self):
        for i in self.products_tree.get_children():
            self.products_tree.delete(i)
        self.products = self.db.get_all_products()
        for p in self.products:
            self.products_tree.insert('', 'end', values=(p[0], p[1], p[4], p[5]))

    def add_to_cart(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для добавления.")
            return
        product_id = int(self.products_tree.item(selected[0])['values'][0])
        product = self.db.get_product_by_id(product_id)
        if product is None:
            messagebox.showerror("Ошибка", "Товар не найден.")
            return
        qty = self.qty_var.get()
        if qty <= 0:
            messagebox.showwarning("Внимание", "Количество должно быть положительным.")
            return
        if qty > product[5]:
            messagebox.showwarning("Внимание", f"На складе недостаточно товара. Доступно: {product[5]}")
            return

        # Если товар уже в корзине, увеличить количество
        for idx, item in enumerate(self.cart):
            if item[0] == product_id:
                new_amount = item[3] + qty
                if new_amount > product[5]:
                    messagebox.showwarning("Внимание", f"На складе недостаточно товара. Доступно: {product[5]}")
                    return
                self.cart[idx] = (product_id, product[1], product[4], new_amount)
                break
        else:
            self.cart.append((product_id, product[1], product[4], qty))

        self.refresh_cart()

    def refresh_cart(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        total = 0
        for item in self.cart:
            sum_ = item[2] * item[3]
            total += sum_
            self.cart_tree.insert('', 'end', values=(item[1], f"{item[2]:.2f}", item[3], f"{sum_:.2f}"))
        self.total_var.set(f"Итого: {total:.2f}")

    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для удаления.")
            return
        item_idx = self.cart_tree.index(selected[0])
        del self.cart[item_idx]
        self.refresh_cart()

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Внимание", "Корзина пуста.")
            return

        # Окно оплаты
        pay_window = PaymentWindow(self, self.db, self.cart, self.refresh_products, self.clear_cart)
        pay_window.grab_set()

    def clear_cart(self):
        self.cart.clear()
        self.refresh_cart()

    def on_close(self):
        self.master.child_windows.remove(self)
        self.destroy()


class PaymentWindow(tk.Toplevel):
    def __init__(self, master, db, cart, refresh_products_callback, clear_cart_callback):
        super().__init__(master)
        self.db = db
        self.cart = cart
        self.refresh_products_callback = refresh_products_callback
        self.clear_cart_callback = clear_cart_callback

        self.title("Оплата")
        self.geometry("300x300")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Сумма к оплате
        self.total_sum = sum(item[2]*item[3] for item in cart)
        tk.Label(self, text=f"Сумма к оплате: {self.total_sum:.2f}", font=("Arial", 14)).pack(pady=10)

        # Тип оплаты
        tk.Label(self, text="Тип оплаты:").pack()
        self.payment_types = self.db.get_payment_types()
        self.payment_var = tk.IntVar()
        self.payment_var.set(self.payment_types[0][0])
        for pt in self.payment_types:
            tk.Radiobutton(self, text=pt[1], variable=self.payment_var, value=pt[0]).pack(anchor='w')

        # Внесенная сумма
        tk.Label(self, text="Внесенная сумма:").pack()
        self.payed_var = tk.DoubleVar(value=self.total_sum)
        self.payed_entry = tk.Entry(self, textvariable=self.payed_var)
        self.payed_entry.pack()

        # Кнопка оплатить
        btn_pay = tk.Button(self, text="Оплатить", command=self.pay)
        btn_pay.pack(pady=20)

    def pay(self):
        payed = self.payed_var.get()
        if payed < self.total_sum:
            messagebox.showwarning("Внимание", "Внесенная сумма меньше суммы к оплате.")
            return
        refused = payed - self.total_sum

        # Создаем чек
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        check_id = self.db.create_check(date_str, 1, self.payment_var.get(), self.total_sum, payed, refused)

        # Добавляем товары в чек и уменьшаем склад
        for item in self.cart:
            product_id, name, price, amount = item
            self.db.add_product_to_check(product_id, amount, check_id)

            # Обновляем количество на складе
            product = self.db.get_product_by_id(product_id)
            new_amount = product[5] - amount
            self.db.update_product_amount(product_id, new_amount)

        messagebox.showinfo("Успех", f"Оплата прошла успешно. Сдача: {refused:.2f}")
        self.refresh_products_callback()
        self.clear_cart_callback()
        self.destroy()

    def on_close(self):
        self.destroy()


class WarehouseWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Склад")
        self.geometry("600x400")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Таблица товаров
        self.tree = ttk.Treeview(self, columns=('id', 'name', 'code', 'buy_price', 'sale_price', 'amount'), show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Наименование')
        self.tree.heading('code', text='Код')
        self.tree.heading('buy_price', text='Цена закупки')
        self.tree.heading('sale_price', text='Цена продажи')
        self.tree.heading('amount', text='Количество')
        self.tree.column('id', width=30)
        self.tree.column('name', width=150)
        self.tree.column('code', width=100)
        self.tree.column('buy_price', width=80)
        self.tree.column('sale_price', width=80)
        self.tree.column('amount', width=80)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Кнопка добавить товар
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X)

        btn_add = tk.Button(btn_frame, text="Добавить товар", command=self.add_product)
        btn_add.pack(side=tk.LEFT, padx=5, pady=5)

        btn_edit = tk.Button(btn_frame, text="Редактировать товар", command=self.edit_product)
        btn_edit.pack(side=tk.LEFT, padx=5, pady=5)

        btn_refresh = tk.Button(btn_frame, text="Обновить", command=self.refresh_products)
        btn_refresh.pack(side=tk.LEFT, padx=5, pady=5)

        self.refresh_products()

    def refresh_products(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        products = self.db.get_all_products()
        for p in products:
            self.tree.insert('', 'end', values=p)

    def add_product(self):
        ProductEditWindow(self, self.db, self.refresh_products)

    def edit_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для редактирования.")
            return
        item = self.tree.item(selected[0])['values']
        ProductEditWindow(self, self.db, self.refresh_products, product=item)

    def on_close(self):
        self.master.child_windows.remove(self)
        self.destroy()


class ProductEditWindow(tk.Toplevel):
    def __init__(self, master, db, refresh_callback, product=None):
        super().__init__(master)
        self.db = db
        self.refresh_callback = refresh_callback
        self.product = product

        self.title("Редактирование товара" if product else "Добавление товара")
        self.geometry("400x300")

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


class AnalysisWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Анализ")
        self.geometry("600x400")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Для примера - покажем список чеков с суммами
        self.tree = ttk.Treeview(self, columns=('id', 'date', 'status', 'payment_type', 'sum', 'payed_sum', 'refused_sum'), show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('date', text='Дата')
        self.tree.heading('status', text='Статус')
        self.tree.heading('payment_type', text='Тип оплаты')
        self.tree.heading('sum', text='Сумма')
        self.tree.heading('payed_sum', text='Внесено')
        self.tree.heading('refused_sum', text='Сдача')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.refresh_data()

    def refresh_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        c = self.db.conn.cursor()
        c.execute('''
            SELECT checks.id, checks.date, checks.status, payment_type.name, checks.sum, checks.payed_sum, checks.refused_sum
            FROM checks LEFT JOIN payment_type ON checks.payment_type = payment_type.id
            ORDER BY checks.date DESC
        ''')
        rows = c.fetchall()
        status_map = {0: 'Ожидание оплаты', 1: 'Покупка', 2: 'Возврат'}
        for r in rows:
            self.tree.insert('', 'end', values=(
                r[0], r[1], status_map.get(r[2], 'Неизвестно'), r[3], f"{r[4]:.2f}", f"{r[5]:.2f}", f"{r[6]:.2f}"
            ))

    def on_close(self):
        self.master.child_windows.remove(self)
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Учет и торговля рыболовными товарами")
        self.geometry("300x150")

        self.db = Database()
        self.child_windows = []

        btn_cash = tk.Button(self, text="Касса", width=20, command=self.open_cash_register)
        btn_cash.pack(pady=5)

        btn_warehouse = tk.Button(self, text="Склад", width=20, command=self.open_warehouse)
        btn_warehouse.pack(pady=5)

        btn_analysis = tk.Button(self, text="Анализ", width=20, command=self.open_analysis)
        btn_analysis.pack(pady=5)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def open_cash_register(self):
        win = CashRegisterWindow(self, self.db)
        self.child_windows.append(win)

    def open_warehouse(self):
        win = WarehouseWindow(self, self.db)
        self.child_windows.append(win)

    def open_analysis(self):
        win = AnalysisWindow(self, self.db)
        self.child_windows.append(win)

    def on_close(self):
        if self.child_windows:
            messagebox.showwarning("Внимание", "Закройте все дочерние окна перед выходом.")
            return
        self.db.close()
        self.destroy()


if __name__ == '__main__':
    app = App()
    app.mainloop()
