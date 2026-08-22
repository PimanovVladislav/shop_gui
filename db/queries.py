"""Именованные SQL-запросы. Единственное место хранения строк SQL."""

# ── DDL / миграции ───────────────────────────────────────────────────────────

CREATE_TABLE_PRODUCTS = '''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        code TEXT,
        buy_price REAL,
        sale_price REAL,
        amount INTEGER,
        deleted INTEGER DEFAULT 0,
        purchase_date TEXT,
        supplier TEXT DEFAULT ''
    )
'''

CREATE_TABLE_PAYMENT_TYPE = '''
    CREATE TABLE IF NOT EXISTS payment_type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
'''

CREATE_TABLE_CHECKS = '''
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
'''

CREATE_TABLE_CHECK_PRODUCTS = '''
    CREATE TABLE IF NOT EXISTS check_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        amount INTEGER,
        id_check INTEGER,
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(id_check) REFERENCES checks(id)
    )
'''

COUNT_PAYMENT_TYPES = 'SELECT COUNT(*) FROM payment_type'
INSERT_PAYMENT_TYPE = 'INSERT INTO payment_type (name) VALUES (?)'

PRAGMA_TABLE_INFO_CHECKS = 'PRAGMA table_info(checks)'
PRAGMA_TABLE_INFO_PRODUCTS = 'PRAGMA table_info(products)'
ALTER_CHECKS_ADD_RECEIPT_TEXT = (
    "ALTER TABLE checks ADD COLUMN receipt_text TEXT DEFAULT ''"
)
ALTER_PRODUCTS_ADD_PURCHASE_DATE = (
    'ALTER TABLE products ADD COLUMN purchase_date TEXT'
)
ALTER_PRODUCTS_ADD_SUPPLIER = (
    'ALTER TABLE products ADD COLUMN supplier TEXT DEFAULT \'\''
)

CREATE_INDEX_PRODUCTS_DELETED = (
    'CREATE INDEX IF NOT EXISTS idx_products_deleted ON products(deleted)'
)
CREATE_INDEX_CHECKS_DATE = (
    'CREATE INDEX IF NOT EXISTS idx_checks_date ON checks(date)'
)
CREATE_INDEX_CP_CHECK = (
    'CREATE INDEX IF NOT EXISTS idx_cp_check ON check_products(id_check)'
)
CREATE_INDEX_CP_PRODUCT = (
    'CREATE INDEX IF NOT EXISTS idx_cp_product ON check_products(product_id)'
)
PRAGMA_JOURNAL_WAL = 'PRAGMA journal_mode=WAL'
PRAGMA_SYNCHRONOUS_NORMAL = 'PRAGMA synchronous=NORMAL'

# ── Товары ───────────────────────────────────────────────────────────────────

PRODUCT_SELECT_ALL = '''
    SELECT id, code, name, buy_price, sale_price, amount, purchase_date, supplier
    FROM products WHERE deleted = 0
'''

PRODUCT_SELECT_AVAILABLE = '''
    SELECT id, code, name, buy_price, sale_price, amount, purchase_date, supplier
    FROM products WHERE amount > 0 AND deleted = 0
'''

PRODUCT_SELECT_NOT_AVAILABLE = '''
    SELECT id, code, name, buy_price, sale_price, amount, purchase_date, supplier
    FROM products WHERE amount = 0 AND deleted = 0
'''

PRODUCT_INSERT = '''
    INSERT INTO products (name, code, buy_price, sale_price, amount, purchase_date, supplier)
    VALUES (?, ?, ?, ?, ?, ?, ?)
'''

PRODUCT_UPDATE = '''
    UPDATE products SET name=?, code=?, buy_price=?, sale_price=?,
           amount=?, purchase_date=?, supplier=? WHERE id=?
'''

PRODUCT_UPDATE_AMOUNT = (
    'UPDATE products SET amount = ? WHERE id = ?'
)

PRODUCT_SOFT_DELETE = (
    'UPDATE products SET deleted = 1 WHERE id = ?'
)

PRODUCT_SELECT_BY_ID = (
    'SELECT * FROM products WHERE id = ?'
)

PRODUCT_SELECT_AMOUNT = (
    'SELECT amount FROM products WHERE id = ?'
)

PRODUCT_SELECT_AMOUNT_AND_PRICE = (
    'SELECT amount, sale_price FROM products WHERE id = ?'
)

# ── Типы оплаты ──────────────────────────────────────────────────────────────

PAYMENT_TYPE_SELECT_ALL = 'SELECT * FROM payment_type'

# ── Чеки ─────────────────────────────────────────────────────────────────────

CHECK_INSERT = '''
    INSERT INTO checks (date, status, payment_type, sum, payed_sum, refused_sum)
    VALUES (?, ?, ?, ?, ?, ?)
'''

CHECK_INSERT_WRITEOFF = '''
    INSERT INTO checks (date, status, payment_type, sum, payed_sum, refused_sum)
    VALUES (?, ?, ?, ?, 0, 0)
'''

CHECK_INSERT_RETURN = '''
    INSERT INTO checks (date, status, payment_type, sum, payed_sum, refused_sum)
    VALUES (?, ?, ?, 0, 0, 0)
'''

CHECK_UPDATE_RECEIPT_TEXT = (
    'UPDATE checks SET receipt_text = ? WHERE id = ?'
)

CHECK_SELECT_RECEIPT_TEXT = (
    'SELECT date, receipt_text FROM checks WHERE id = ?'
)

CHECK_SELECT_PAYMENT_TYPE = (
    'SELECT payment_type FROM checks WHERE id = ?'
)

CHECK_UPDATE_RETURN_SUMS = (
    'UPDATE checks SET refused_sum = ?, sum = ? WHERE id = ?'
)

CHECK_SELECT_ALL = '''
    SELECT checks.id, strftime('%d.%m.%Y %H:%M', checks.date),
           checks.status, payment_type.name,
           checks.sum, checks.payed_sum, checks.refused_sum
    FROM checks LEFT JOIN payment_type
    ON checks.payment_type = payment_type.id
    ORDER BY checks.date DESC
'''

# ── Позиции чека ─────────────────────────────────────────────────────────────

CHECK_PRODUCT_INSERT = '''
    INSERT INTO check_products (product_id, amount, id_check)
    VALUES (?, ?, ?)
'''

CHECK_PRODUCT_INSERT_RETURN = '''
    INSERT INTO check_products (id_check, product_id, amount)
    VALUES (?, ?, ?)
'''

CHECK_PRODUCT_SELECT_BY_CHECK = '''
    SELECT cp.id, p.id, p.name, p.code, cp.amount, p.sale_price
    FROM check_products cp
    JOIN products p ON cp.product_id = p.id
    WHERE cp.id_check = ?
'''

CHECK_PRODUCT_SELECT_PRODUCT_ID = (
    'SELECT product_id FROM check_products WHERE id = ?'
)

CHECK_PRODUCT_SELECT_BY_CHECK_SIMPLE = '''
    SELECT product_id, amount FROM check_products WHERE id_check = ?
'''

# ── Анализ продаж ────────────────────────────────────────────────────────────

SALES_ANALYSIS = '''
    SELECT
        p.code,
        p.name,
        MAX(CASE WHEN ch.status = 1 THEN ch.date END) AS last_sale_date,
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
    WHERE p.deleted = 0
    GROUP BY p.id, p.code, p.name, p.amount
    ORDER BY p.name
'''
