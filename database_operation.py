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