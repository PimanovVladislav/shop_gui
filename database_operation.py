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
        c.execute("SELECT id, code, name, buy_price, sale_price, amount FROM products")
        return c.fetchall()

    def get_available_products(self):
        c = self.conn.cursor()
        c.execute("SELECT id, code, name, buy_price, sale_price, amount FROM products WHERE amount > 0")
        return c.fetchall()

    def get_not_available_products(self):
        c = self.conn.cursor()
        c.execute("SELECT id, code, name, buy_price, sale_price, amount FROM products WHERE amount = 0")
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

    def delete_product(self, product_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()