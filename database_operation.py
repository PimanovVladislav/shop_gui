import sqlite3
import os
from datetime import datetime

DB_NAME = 'fish_store.db'

# Статусы чеков: 0 — ожидание, 1 — продажа, 2 — возврат, 3 — списание
CHECK_STATUS_SALE = 1
CHECK_STATUS_RETURN = 2
CHECK_STATUS_WRITEOFF = 3


class Database:
    def __init__(self):
        if os.name == 'nt':
            app_data_path = os.getenv('APPDATA')
        else:
            app_data_path = os.path.expanduser('~')
            app_data_path = os.path.join(app_data_path, '.config')

        db_dir = os.path.join(app_data_path, 'FishStore')
        os.makedirs(db_dir, exist_ok=True)

        db_path = os.path.join(db_dir, 'fish_store.db')

        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        self._migrate()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                code TEXT,
                buy_price REAL,
                sale_price REAL,
                amount INTEGER,
                deleted INTEGER DEFAULT 0
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
                receipt_text TEXT DEFAULT '',
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
        c.execute("SELECT COUNT(*) FROM payment_type")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO payment_type (name) VALUES (?)",
                          [('Наличные',), ('Карта',), ('Электронный кошелек',)])
        self.conn.commit()

    def _migrate(self):
        c = self.conn.cursor()
        c.execute("PRAGMA table_info(checks)")
        cols = [row[1] for row in c.fetchall()]
        if 'receipt_text' not in cols:
            c.execute("ALTER TABLE checks ADD COLUMN receipt_text TEXT DEFAULT ''")
        c.execute("PRAGMA table_info(products)")
        cols = [row[1] for row in c.fetchall()]
        if 'purchase_date' not in cols:
            c.execute("ALTER TABLE products ADD COLUMN purchase_date TEXT")
        self.conn.commit()

    def get_all_products(self):
        c = self.conn.cursor()
        c.execute(
            "SELECT id, code, name, buy_price, sale_price, amount, purchase_date "
            "FROM products WHERE deleted = 0"
        )
        return c.fetchall()

    def get_available_products(self):
        c = self.conn.cursor()
        c.execute(
            "SELECT id, code, name, buy_price, sale_price, amount, purchase_date "
            "FROM products WHERE amount > 0 AND deleted = 0"
        )
        return c.fetchall()

    def get_not_available_products(self):
        c = self.conn.cursor()
        c.execute(
            "SELECT id, code, name, buy_price, sale_price, amount, purchase_date "
            "FROM products WHERE amount = 0 AND deleted = 0"
        )
        return c.fetchall()

    def add_product(self, name, code, buy_price, sale_price, amount, purchase_date=None):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO products (name, code, buy_price, sale_price, amount, purchase_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, code, buy_price, sale_price, amount, purchase_date)
        )
        self.conn.commit()
        return c.lastrowid

    def update_product_amount(self, product_id, new_amount):
        c = self.conn.cursor()
        c.execute("UPDATE products SET amount = ? WHERE id = ?", (new_amount, product_id))
        self.conn.commit()

    def get_product_by_id(self, product_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return c.fetchone()

    def get_payment_types(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM payment_type")
        return c.fetchall()

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

    def save_receipt_text(self, check_id, receipt_text):
        c = self.conn.cursor()
        c.execute("UPDATE checks SET receipt_text = ? WHERE id = ?",
                  (receipt_text, check_id))
        self.conn.commit()

    def get_receipt_text(self, check_id):
        c = self.conn.cursor()
        c.execute("SELECT date, receipt_text FROM checks WHERE id = ?", (check_id,))
        return c.fetchone()

    def write_off_product(self, product_id, amount):
        product = self.get_product_by_id(product_id)
        if not product or amount <= 0:
            raise ValueError("Некорректные данные для списания")
        if amount > product[5]:
            raise ValueError(f"Недостаточно на складе. Доступно: {product[5]}")

        payment_types = self.get_payment_types()
        payment_type = payment_types[0][0] if payment_types else 1

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sum_ = product[4] * amount
        check_id = self.create_check(
            date_str, CHECK_STATUS_WRITEOFF, payment_type, sum_, 0, 0
        )
        self.add_product_to_check(product_id, amount, check_id)
        self.update_product_amount(product_id, product[5] - amount)
        return check_id

    def get_sales_analysis(self, date_from: datetime, date_to: datetime):
        """
        Анализ продаж за период.
        Кортеж: (code, name, last_sale_date, sold_qty, returned_qty, net_qty,
                 stock_qty, sold_sum, returned_sum, net_sum)
        """
        c = self.conn.cursor()

        date_from_str = date_from.strftime("%Y-%m-%d 00:00:00")
        date_to_str = date_to.strftime("%Y-%m-%d 23:59:59")

        query = """
            SELECT
                p.code,
                p.name,
                (SELECT MAX(ch2.date)
                 FROM check_products cp2
                 JOIN checks ch2 ON cp2.id_check = ch2.id
                 WHERE cp2.product_id = p.id AND ch2.status = 1) AS last_sale_date,
                IFNULL(SUM(CASE WHEN ch.status = 1 THEN cp.amount ELSE 0 END), 0) AS sold_qty,
                IFNULL(SUM(CASE WHEN ch.status = 2 THEN cp.amount ELSE 0 END), 0) AS returned_qty,
                IFNULL(SUM(CASE WHEN ch.status = 1 THEN cp.amount ELSE 0 END), 0)
                    - IFNULL(SUM(CASE WHEN ch.status = 2 THEN cp.amount ELSE 0 END), 0) AS net_qty,
                p.amount AS stock_qty,
                IFNULL(SUM(CASE WHEN ch.status = 1 THEN cp.amount * p.sale_price ELSE 0 END), 0) AS sold_sum,
                IFNULL(SUM(CASE WHEN ch.status = 2 THEN cp.amount * p.sale_price ELSE 0 END), 0) AS returned_sum,
                IFNULL(SUM(CASE WHEN ch.status = 1 THEN cp.amount * p.sale_price ELSE 0 END), 0)
                    - IFNULL(SUM(CASE WHEN ch.status = 2 THEN cp.amount * p.sale_price ELSE 0 END), 0) AS net_sum
            FROM products p
            JOIN check_products cp ON p.id = cp.product_id
            JOIN checks ch ON cp.id_check = ch.id AND ch.date BETWEEN ? AND ?
            GROUP BY p.id, p.name, p.amount
            ORDER BY p.name
        """
        c.execute(query, (date_from_str, date_to_str))
        return c.fetchall()

    def close(self):
        self.conn.close()

    def delete_product(self, product_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE products SET deleted = 1 WHERE id = ?", (product_id,))
        self.conn.commit()
