#!/usr/bin/env python3
"""Create and populate the TPC-C benchmark SQLite database."""

import sqlite3
import os
from random import choice, randint
from datetime import datetime
from settings import DB_PATH, AMOUNT_OF_WAREHOUSES

DDL = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS warehouse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER NOT NULL,
    street_1 TEXT NOT NULL,
    street_2 TEXT NOT NULL,
    city TEXT NOT NULL,
    w_zip TEXT NOT NULL,
    tax REAL NOT NULL,
    ytd REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS district (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL REFERENCES warehouse(id),
    name TEXT NOT NULL,
    street_1 TEXT NOT NULL,
    street_2 TEXT NOT NULL,
    city TEXT NOT NULL,
    d_zip TEXT NOT NULL,
    tax REAL NOT NULL,
    ytd REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS customer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    middle_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    street_1 TEXT NOT NULL,
    street_2 TEXT NOT NULL,
    city TEXT NOT NULL,
    c_zip TEXT NOT NULL,
    phone TEXT NOT NULL,
    since TEXT NOT NULL,
    credit TEXT NOT NULL,
    credit_lim REAL NOT NULL,
    discount REAL NOT NULL,
    delivery_cnt INTEGER NOT NULL DEFAULT 0,
    payment_cnt INTEGER NOT NULL DEFAULT 0,
    balance REAL NOT NULL DEFAULT 1000000,
    ytd_payment REAL NOT NULL DEFAULT 0,
    data1 TEXT NOT NULL,
    data2 TEXT NOT NULL,
    district_id INTEGER NOT NULL REFERENCES district(id)
);

CREATE TABLE IF NOT EXISTS item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL REFERENCES warehouse(id),
    item_id INTEGER NOT NULL REFERENCES item(id),
    quantity INTEGER NOT NULL,
    ytd REAL NOT NULL,
    order_cnt INTEGER NOT NULL DEFAULT 0,
    remote_cnt INTEGER NOT NULL DEFAULT 0,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL REFERENCES warehouse(id),
    district_id INTEGER NOT NULL REFERENCES district(id),
    ol_cnt INTEGER NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customer(id),
    entry_d TEXT NOT NULL,
    is_o_delivered INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS order_line (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_d TEXT,
    item_id INTEGER NOT NULL REFERENCES item(id),
    amount INTEGER NOT NULL,
    order_id INTEGER NOT NULL REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    data TEXT NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customer(id)
);

CREATE INDEX IF NOT EXISTS idx_district_warehouse ON district(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_customer_district ON customer(district_id);
CREATE INDEX IF NOT EXISTS idx_stock_warehouse ON stock(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_item ON stock(item_id);
CREATE INDEX IF NOT EXISTS idx_orders_warehouse ON orders(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_orders_district ON orders(district_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_delivered ON orders(is_o_delivered);
CREATE INDEX IF NOT EXISTS idx_order_line_order ON order_line(order_id);
CREATE INDEX IF NOT EXISTS idx_order_line_item ON order_line(item_id);
CREATE INDEX IF NOT EXISTS idx_history_customer ON history(customer_id);
"""

CITIES = ('Moscow', 'St. Petersburg', 'Pushkin', 'Oranienbaum', 'Vladivostok')
NAMES = ('Ivan', 'Evgeniy', 'Alexander', 'Fedor', 'Julia', 'Stephany', 'Sergey', 'Natalya', 'Keanu', 'John', 'Harry', 'James')
LAST_NAMES = ('Petrov', 'Ivanov', 'Andreev', 'Mills', 'Smith', 'Anderson', 'Dominov', 'Tishenko', 'Zhitnikov')
DISCOUNTS = (0, 10, 15, 20, 30)


def populate(conn, n):
    cur = conn.cursor()
    d_cnt = 0

    # Warehouses + Districts
    for i in range(1, n + 1):
        city = choice(CITIES)
        cur.execute(
            "INSERT INTO warehouse (number, street_1, street_2, city, w_zip, tax, ytd) VALUES (?,?,?,?,?,?,?)",
            (i, f'w_st {i}', f'w_st2 {i}', city, f'w_zip {i}', float(i), 0)
        )
        w_id = cur.lastrowid
        for j in range(10):
            cur.execute(
                "INSERT INTO district (warehouse_id, name, street_1, street_2, city, d_zip, tax, ytd) VALUES (?,?,?,?,?,?,?,?)",
                (w_id, f'dist {i} {j}', f'd_st {j}', f'd_st2 {j}', city, f'd_zip {j}', float(j), 0)
            )
            d_cnt += 1

    # Customers
    for i in range(10 * n):
        cur.execute(
            "INSERT INTO customer (first_name, middle_name, last_name, street_1, street_2, city, c_zip, phone, since, credit, credit_lim, discount, delivery_cnt, payment_cnt, balance, ytd_payment, data1, data2, district_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (choice(NAMES), choice(NAMES), choice(LAST_NAMES),
             f'c_st {i}', f'c_st2 {i}', choice(CITIES), f'c_zip {i}',
             'phone', datetime(2005, 7, 14, 12, 30).isoformat(), 'credit',
             randint(1000, 100000), choice(DISCOUNTS),
             0, 0, 1000000, 0,
             f'customer {i}', f'hello {i}',
             randint(1, d_cnt))
        )

    # Items + Stock
    for i in range(1, n * 10 + 1):
        cur.execute(
            "INSERT INTO item (name, price, data) VALUES (?,?,?)",
            (f'item {i}', randint(1, 100000), 'data')
        )
        item_id = cur.lastrowid
        for j in range(1, n + 1):
            cur.execute(
                "INSERT INTO stock (warehouse_id, item_id, quantity, ytd, order_cnt, remote_cnt, data) VALUES (?,?,?,?,?,?,?)",
                (j, item_id, 100000, randint(1, 100000), 0, 0, 'data')
            )

    conn.commit()
    print(f"Populated: {n} warehouses, {d_cnt} districts, {10*n} customers, {10*n} items, {n*10*n} stock records")


def create_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)
    print("Schema created.")
    populate(conn, AMOUNT_OF_WAREHOUSES)
    conn.close()
    print(f"Database ready at {DB_PATH}")


if __name__ == '__main__':
    create_db()
