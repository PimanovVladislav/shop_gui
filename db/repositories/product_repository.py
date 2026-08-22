from db import queries as Q


class ProductRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_all(self):
        c = self.conn.cursor()
        c.execute(Q.PRODUCT_SELECT_ALL)
        return c.fetchall()

    def get_available(self):
        c = self.conn.cursor()
        c.execute(Q.PRODUCT_SELECT_AVAILABLE)
        return c.fetchall()

    def get_not_available(self):
        c = self.conn.cursor()
        c.execute(Q.PRODUCT_SELECT_NOT_AVAILABLE)
        return c.fetchall()

    def get_by_id(self, product_id):
        c = self.conn.cursor()
        c.execute(Q.PRODUCT_SELECT_BY_ID, (product_id,))
        return c.fetchone()

    def add(self, name, code, buy_price, sale_price, amount,
            purchase_date=None, supplier=''):
        c = self.conn.cursor()
        c.execute(
            Q.PRODUCT_INSERT,
            (name, code, buy_price, sale_price, amount, purchase_date, supplier or '')
        )
        self.conn.commit()
        return c.lastrowid

    def update(self, product_id, name, code, buy_price, sale_price, amount,
               purchase_date=None, supplier=''):
        c = self.conn.cursor()
        c.execute(
            Q.PRODUCT_UPDATE,
            (name, code, buy_price, sale_price, amount,
             purchase_date, supplier or '', product_id)
        )
        self.conn.commit()

    def update_amount(self, product_id, new_amount):
        c = self.conn.cursor()
        c.execute(Q.PRODUCT_UPDATE_AMOUNT, (new_amount, product_id))
        self.conn.commit()

    def soft_delete(self, product_id):
        c = self.conn.cursor()
        c.execute(Q.PRODUCT_SOFT_DELETE, (product_id,))
        self.conn.commit()

    def get_amount(self, product_id):
        c = self.conn.cursor()
        c.execute(Q.PRODUCT_SELECT_AMOUNT, (product_id,))
        row = c.fetchone()
        return row[0] if row else None

    def get_amount_and_price(self, product_id):
        c = self.conn.cursor()
        c.execute(Q.PRODUCT_SELECT_AMOUNT_AND_PRICE, (product_id,))
        return c.fetchone()
