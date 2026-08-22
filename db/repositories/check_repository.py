from datetime import datetime

from db import queries as Q
from domain.constants import CHECK_STATUS_RETURN, CHECK_STATUS_WRITEOFF


class CheckRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_all_checks(self):
        c = self.conn.cursor()
        c.execute(Q.CHECK_SELECT_ALL)
        return c.fetchall()

    def get_check_products(self, check_id):
        c = self.conn.cursor()
        c.execute(Q.CHECK_PRODUCT_SELECT_BY_CHECK, (check_id,))
        return c.fetchall()

    def get_payment_type(self, check_id):
        c = self.conn.cursor()
        c.execute(Q.CHECK_SELECT_PAYMENT_TYPE, (check_id,))
        row = c.fetchone()
        return row[0] if row else None

    def get_receipt_text(self, check_id):
        c = self.conn.cursor()
        c.execute(Q.CHECK_SELECT_RECEIPT_TEXT, (check_id,))
        return c.fetchone()

    def save_receipt_text(self, check_id, receipt_text):
        c = self.conn.cursor()
        c.execute(Q.CHECK_UPDATE_RECEIPT_TEXT, (receipt_text, check_id))
        self.conn.commit()

    def get_payment_types(self):
        c = self.conn.cursor()
        c.execute(Q.PAYMENT_TYPE_SELECT_ALL)
        return c.fetchall()

    def create_check(self, date, status, payment_type, sum_, payed_sum, refused_sum):
        c = self.conn.cursor()
        c.execute(
            Q.CHECK_INSERT,
            (date, status, payment_type, sum_, payed_sum, refused_sum)
        )
        self.conn.commit()
        return c.lastrowid

    def add_product_to_check(self, product_id, amount, check_id):
        c = self.conn.cursor()
        c.execute(Q.CHECK_PRODUCT_INSERT, (product_id, amount, check_id))
        self.conn.commit()

    def process_sale(self, date_str, status, payment_type, total_sum, payed,
                     refused, items, receipt_text=None):
        c = self.conn.cursor()
        try:
            c.execute(
                Q.CHECK_INSERT,
                (date_str, status, payment_type, total_sum, payed, refused)
            )
            check_id = c.lastrowid
            for product_id, amount in items:
                c.execute(Q.CHECK_PRODUCT_INSERT, (product_id, amount, check_id))
                c.execute(Q.PRODUCT_SELECT_AMOUNT, (product_id,))
                row = c.fetchone()
                if row is None:
                    raise ValueError(f'Товар {product_id} не найден')
                new_amount = row[0] - amount
                if new_amount < 0:
                    raise ValueError(f'Недостаточно товара {product_id} на складе')
                c.execute(Q.PRODUCT_UPDATE_AMOUNT, (new_amount, product_id))
            if receipt_text is not None:
                c.execute(Q.CHECK_UPDATE_RECEIPT_TEXT, (receipt_text, check_id))
            self.conn.commit()
            return check_id
        except Exception:
            self.conn.rollback()
            raise

    def write_off_product(self, product_repo, product_id, amount):
        product = product_repo.get_by_id(product_id)
        if not product or amount <= 0:
            raise ValueError('Некорректные данные для списания')
        if amount > product[5]:
            raise ValueError(f'Недостаточно на складе. Доступно: {product[5]}')

        payment_types = self.get_payment_types()
        payment_type = payment_types[0][0] if payment_types else 1
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sum_ = product[4] * amount

        c = self.conn.cursor()
        try:
            c.execute(
                Q.CHECK_INSERT_WRITEOFF,
                (date_str, CHECK_STATUS_WRITEOFF, payment_type, sum_)
            )
            check_id = c.lastrowid
            c.execute(Q.CHECK_PRODUCT_INSERT, (product_id, amount, check_id))
            c.execute(Q.PRODUCT_UPDATE_AMOUNT, (product[5] - amount, product_id))
            self.conn.commit()
            return check_id
        except Exception:
            self.conn.rollback()
            raise

    def create_return(self, source_check_id, items):
        """items: [(check_product_id, product_id, amount, price), ...]"""
        payment_type = self.get_payment_type(source_check_id)
        if payment_type is None:
            raise ValueError('Чек не найден')

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c = self.conn.cursor()
        try:
            c.execute(Q.CHECK_INSERT_RETURN, (now_str, CHECK_STATUS_RETURN, payment_type))
            new_check_id = c.lastrowid
            total_refund_sum = 0.0
            store_deltas = {}

            for _cp_id, product_id, amount, price in items:
                if amount <= 0:
                    continue
                c.execute(
                    Q.CHECK_PRODUCT_INSERT_RETURN,
                    (new_check_id, product_id, amount)
                )
                c.execute(Q.PRODUCT_SELECT_AMOUNT, (product_id,))
                current_amount = c.fetchone()[0]
                c.execute(
                    Q.PRODUCT_UPDATE_AMOUNT,
                    (current_amount + amount, product_id)
                )
                store_deltas[product_id] = store_deltas.get(product_id, 0) + amount
                total_refund_sum += price * amount

            c.execute(
                Q.CHECK_UPDATE_RETURN_SUMS,
                (total_refund_sum, -total_refund_sum, new_check_id)
            )
            self.conn.commit()
            return new_check_id, total_refund_sum, store_deltas
        except Exception:
            self.conn.rollback()
            raise

    def get_product_id_for_check_product(self, cp_id):
        c = self.conn.cursor()
        c.execute(Q.CHECK_PRODUCT_SELECT_PRODUCT_ID, (cp_id,))
        row = c.fetchone()
        return row[0] if row else None

    def get_check_products_for_return(self, check_id):
        c = self.conn.cursor()
        c.execute(Q.CHECK_PRODUCT_SELECT_BY_CHECK_SIMPLE, (check_id,))
        return c.fetchall()
