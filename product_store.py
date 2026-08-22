"""Кэш товаров в памяти — единый источник данных для UI."""


class ProductStore:
    """Строка списка: (id, code, name, buy_price, sale_price, amount, purchase_date, supplier)."""

    def __init__(self, db):
        self.db = db
        self._by_id = {}
        self.reload()

    def reload(self):
        self._by_id.clear()
        for row in self.db.get_all_products():
            self._by_id[row[0]] = row

    def get(self, product_id):
        return self._by_id.get(int(product_id))

    def get_db_row(self, product_id):
        """Формат как у Database.get_product_by_id: (id, name, code, ...)."""
        p = self.get(product_id)
        if p is None:
            return None
        purchase_date = p[6] if len(p) > 6 else None
        supplier = p[7] if len(p) > 7 else ''
        return (p[0], p[2], p[1], p[3], p[4], p[5], 0, purchase_date, supplier or '')

    def get_all(self):
        return list(self._by_id.values())

    def get_available(self):
        return [p for p in self._by_id.values() if p[5] > 0]

    def get_not_available(self):
        return [p for p in self._by_id.values() if p[5] == 0]

    def add(self, name, code, buy_price, sale_price, amount,
            purchase_date=None, supplier=''):
        product_id = self.db.add_product(
            name, code, buy_price, sale_price, amount, purchase_date, supplier
        )
        row = (product_id, code, name, buy_price, sale_price, amount,
               purchase_date, supplier or '')
        self._by_id[product_id] = row
        return product_id

    def update(self, product_id, name, code, buy_price, sale_price, amount,
               purchase_date=None, supplier=''):
        self.db.products.update(
            product_id, name, code, buy_price, sale_price, amount,
            purchase_date, supplier
        )
        self._by_id[product_id] = (
            product_id, code, name, buy_price, sale_price, amount,
            purchase_date, supplier or ''
        )

    def update_amount(self, product_id, new_amount):
        self.db.update_product_amount(product_id, new_amount)
        p = self._by_id.get(product_id)
        if p:
            purchase_date = p[6] if len(p) > 6 else None
            supplier = p[7] if len(p) > 7 else ''
            self._by_id[product_id] = (
                p[0], p[1], p[2], p[3], p[4], new_amount, purchase_date, supplier
            )

    def apply_amount_delta(self, product_id, delta):
        p = self.get(product_id)
        if p is None:
            return
        self.update_amount(product_id, p[5] + delta)

    def apply_amount_deltas(self, deltas):
        for product_id, delta in deltas.items():
            self.apply_amount_delta(product_id, delta)

    def delete(self, product_id):
        self.db.delete_product(product_id)
        self._by_id.pop(int(product_id), None)
