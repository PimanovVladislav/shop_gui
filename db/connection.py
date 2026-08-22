import os
import sqlite3
from datetime import datetime

from config.settings import APP_NAME, DB_FILENAME
from db import queries as Q
from db.repositories.analysis_repository import AnalysisRepository
from db.repositories.check_repository import CheckRepository
from db.repositories.product_repository import ProductRepository
from domain.constants import CHECK_STATUS_SALE, CHECK_STATUS_RETURN, CHECK_STATUS_WRITEOFF


class Database:
    """Подключение к SQLite и фасад над репозиториями."""

    def __init__(self):
        if os.name == 'nt':
            app_data_path = os.getenv('APPDATA')
        else:
            app_data_path = os.path.join(os.path.expanduser('~'), '.config')

        db_dir = os.path.join(app_data_path, APP_NAME)
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, DB_FILENAME)

        self.conn = sqlite3.connect(db_path)
        self.products = ProductRepository(self.conn)
        self.checks = CheckRepository(self.conn)
        self.analysis = AnalysisRepository(self.conn)

        self._create_tables()
        self._migrate()

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute(Q.CREATE_TABLE_PRODUCTS)
        c.execute(Q.CREATE_TABLE_PAYMENT_TYPE)
        c.execute(Q.CREATE_TABLE_CHECKS)
        c.execute(Q.CREATE_TABLE_CHECK_PRODUCTS)
        c.execute(Q.COUNT_PAYMENT_TYPES)
        if c.fetchone()[0] == 0:
            c.executemany(
                Q.INSERT_PAYMENT_TYPE,
                [('Наличные',), ('Карта',), ('Электронный кошелек',)]
            )
        self.conn.commit()

    def _migrate(self):
        c = self.conn.cursor()
        c.execute(Q.PRAGMA_TABLE_INFO_CHECKS)
        cols = [row[1] for row in c.fetchall()]
        if 'receipt_text' not in cols:
            c.execute(Q.ALTER_CHECKS_ADD_RECEIPT_TEXT)
        c.execute(Q.PRAGMA_TABLE_INFO_PRODUCTS)
        cols = [row[1] for row in c.fetchall()]
        if 'purchase_date' not in cols:
            c.execute(Q.ALTER_PRODUCTS_ADD_PURCHASE_DATE)
        if 'supplier' not in cols:
            c.execute(Q.ALTER_PRODUCTS_ADD_SUPPLIER)
        c.execute(Q.CREATE_INDEX_PRODUCTS_DELETED)
        c.execute(Q.CREATE_INDEX_CHECKS_DATE)
        c.execute(Q.CREATE_INDEX_CP_CHECK)
        c.execute(Q.CREATE_INDEX_CP_PRODUCT)
        c.execute(Q.PRAGMA_JOURNAL_WAL)
        c.execute(Q.PRAGMA_SYNCHRONOUS_NORMAL)
        self.conn.commit()

    # ── Товары (делегирование) ───────────────────────────────────────────────

    def get_all_products(self):
        return self.products.get_all()

    def get_available_products(self):
        return self.products.get_available()

    def get_not_available_products(self):
        return self.products.get_not_available()

    def add_product(self, name, code, buy_price, sale_price, amount,
                    purchase_date=None, supplier=''):
        return self.products.add(
            name, code, buy_price, sale_price, amount, purchase_date, supplier
        )

    def update_product_amount(self, product_id, new_amount):
        self.products.update_amount(product_id, new_amount)

    def get_product_by_id(self, product_id):
        return self.products.get_by_id(product_id)

    def delete_product(self, product_id):
        self.products.soft_delete(product_id)

    # ── Чеки ─────────────────────────────────────────────────────────────────

    def get_payment_types(self):
        return self.checks.get_payment_types()

    def create_check(self, date, status, payment_type, sum_, payed_sum, refused_sum):
        return self.checks.create_check(date, status, payment_type, sum_, payed_sum, refused_sum)

    def add_product_to_check(self, product_id, amount, id_check):
        self.checks.add_product_to_check(product_id, amount, id_check)

    def save_receipt_text(self, check_id, receipt_text):
        self.checks.save_receipt_text(check_id, receipt_text)

    def get_receipt_text(self, check_id):
        return self.checks.get_receipt_text(check_id)

    def write_off_product(self, product_id, amount):
        return self.checks.write_off_product(self.products, product_id, amount)

    def process_sale(self, date_str, status, payment_type, total_sum, payed,
                     refused, items, receipt_text=None):
        return self.checks.process_sale(
            date_str, status, payment_type, total_sum, payed, refused,
            items, receipt_text
        )

    def get_all_checks(self):
        return self.checks.get_all_checks()

    # ── Анализ ───────────────────────────────────────────────────────────────

    def get_sales_analysis(self, date_from: datetime, date_to: datetime):
        date_from_str = date_from.strftime('%Y-%m-%d 00:00:00')
        date_to_str = date_to.strftime('%Y-%m-%d 23:59:59')
        return self.analysis.get_sales_analysis(date_from_str, date_to_str)

    def close(self):
        self.conn.close()
