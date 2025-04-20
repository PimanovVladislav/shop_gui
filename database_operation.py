import sqlite3
import datetime

def get_timestamp(y,m,d):
    return datetime.datetime.timestamp((datetime.datetime(y,m,d)))

def get_date(tmstmp):
    return datetime.datetime.fromtimestamp(tmstmp).date()

def get_products():
    with sqlite3.connect('db/database.db') as db:
        cursor = db.cursor()
        query = """SELECT id, name, buy_price, sale_price, amount FROM products"""
        cursor.execute(query)
        return list(cursor)

def get_checks():
    with sqlite3.connect('db/database.db') as db:
        cursor = db.cursor()
        query = """SELECT * FROM checks"""
        cursor.execute(query)
        return list(cursor)

def get_checks_products(check_id):
    with sqlite3.connect('db/database.db') as db:
        cursor = db.cursor()
        query = """SELECT * FROM checks_products WHERE check_id IN (?)""".format(check_id)
        cursor.execute(query)
        return list(cursor)

def get_payment_type():
    with sqlite3.connect('db/database.db') as db:
        cursor = db.cursor()
        query = """SELECT id, name FROM payment_type """
        cursor.execute(query)
        return list(cursor)
