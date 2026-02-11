from pony.orm import Database, Required, Set, Optional, PrimaryKey
from datetime import datetime
from settings import DB_PATH

db = Database()


class Warehouse(db.Entity):
    _table_ = 'warehouse'
    number = Required(int)
    street_1 = Required(str)
    street_2 = Required(str)
    city = Required(str)
    w_zip = Required(str)
    tax = Required(float)
    ytd = Required(float, default=0)
    orders = Set("Order")
    districts = Set("District")
    stocks = Set("Stock")


class District(db.Entity):
    _table_ = 'district'
    warehouse = Required(Warehouse, column='warehouse_id')
    name = Required(str)
    street_1 = Required(str)
    street_2 = Required(str)
    city = Required(str)
    d_zip = Required(str)
    tax = Required(float)
    ytd = Required(float, default=0)
    orders = Set("Order")
    customers = Set("Customer")


class Customer(db.Entity):
    _table_ = 'customer'
    first_name = Required(str)
    middle_name = Required(str)
    last_name = Required(str)
    street_1 = Required(str)
    street_2 = Required(str)
    city = Required(str)
    c_zip = Required(str)
    phone = Required(str)
    since = Required(str)
    credit = Required(str)
    credit_lim = Required(float)
    discount = Required(float)
    delivery_cnt = Required(int, default=0)
    payment_cnt = Required(int, default=0)
    balance = Required(float, default=1000000)
    ytd_payment = Required(float, default=0)
    data1 = Required(str)
    data2 = Required(str)
    district = Required(District, column='district_id')
    orders = Set("Order")
    history = Set("History")


class Item(db.Entity):
    _table_ = 'item'
    name = Required(str)
    price = Required(float)
    data = Required(str)
    stocks = Set("Stock")
    o_lns = Set("OrderLine")


class Stock(db.Entity):
    _table_ = 'stock'
    warehouse = Required(Warehouse, column='warehouse_id')
    item = Required(Item, column='item_id')
    quantity = Required(int)
    ytd = Required(float)
    order_cnt = Required(int, default=0)
    remote_cnt = Required(int, default=0)
    data = Required(str)


class Order(db.Entity):
    _table_ = 'orders'
    warehouse = Required(Warehouse, column='warehouse_id')
    district = Required(District, column='district_id')
    ol_cnt = Required(int)
    customer = Required(Customer, column='customer_id')
    entry_d = Required(str)
    is_o_delivered = Required(int, default=0)
    o_lns = Set("OrderLine")


class OrderLine(db.Entity):
    _table_ = 'order_line'
    delivery_d = Optional(str, nullable=True)
    item = Required(Item, column='item_id')
    amount = Required(int)
    order = Required(Order, column='order_id')


class History(db.Entity):
    _table_ = 'history'
    date = Required(str)
    amount = Required(float)
    data = Required(str)
    customer = Required(Customer, column='customer_id')


_initialized = False

def init_db():
    global _initialized
    if _initialized:
        return
    db.bind('sqlite', DB_PATH, create_db=False)
    db.generate_mapping(create_tables=False)
    _initialized = True
