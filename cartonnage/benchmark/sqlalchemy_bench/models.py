from sqlalchemy import (
    Column, Integer, String, Float, Text, ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from settings import DB_PATH

engine = create_engine(
    f'sqlite:///{DB_PATH}',
    connect_args={'timeout': 10},
    pool_pre_ping=True,
)

Base = declarative_base()
Session = sessionmaker(bind=engine)


class Warehouse(Base):
    __tablename__ = 'warehouse'
    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    street_1 = Column(String, nullable=False)
    street_2 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    w_zip = Column(String, nullable=False)
    tax = Column(Float, nullable=False)
    ytd = Column(Float, nullable=False, default=0)
    orders = relationship("Order", backref='warehouse', lazy='dynamic')
    districts = relationship("District", backref='warehouse', lazy='dynamic')
    stocks = relationship("Stock", backref='warehouse', lazy='dynamic')


class District(Base):
    __tablename__ = 'district'
    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'), index=True)
    name = Column(String, nullable=False)
    street_1 = Column(String, nullable=False)
    street_2 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    d_zip = Column(String, nullable=False)
    tax = Column(Float, nullable=False)
    ytd = Column(Float, nullable=False, default=0)
    orders = relationship("Order", backref='district', lazy='dynamic')
    customers = relationship("Customer", backref='district', lazy='dynamic')


class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    street_1 = Column(String, nullable=False)
    street_2 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    c_zip = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    since = Column(String, nullable=False)
    credit = Column(String, nullable=False)
    credit_lim = Column(Float, nullable=False)
    discount = Column(Float, nullable=False)
    delivery_cnt = Column(Integer, nullable=False, default=0)
    payment_cnt = Column(Integer, nullable=False, default=0)
    balance = Column(Float, nullable=False, default=1000000)
    ytd_payment = Column(Float, nullable=False, default=0)
    data1 = Column(Text, nullable=False)
    data2 = Column(Text, nullable=False)
    district_id = Column(Integer, ForeignKey('district.id'), index=True)
    orders = relationship("Order", backref='customer', lazy='dynamic')
    history = relationship("History", backref='customer', lazy='dynamic')


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    data = Column(String, nullable=False)
    stocks = relationship('Stock', backref='item', lazy='dynamic')
    o_lns = relationship("OrderLine", backref='item', lazy='dynamic')


class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'), index=True)
    item_id = Column(Integer, ForeignKey('item.id'), index=True)
    quantity = Column(Integer, nullable=False)
    ytd = Column(Float, nullable=False)
    order_cnt = Column(Integer, nullable=False, default=0)
    remote_cnt = Column(Integer, nullable=False, default=0)
    data = Column(String, nullable=False)


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'), index=True)
    district_id = Column(Integer, ForeignKey('district.id'), index=True)
    ol_cnt = Column(Integer, nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), index=True)
    entry_d = Column(String, nullable=False)
    is_o_delivered = Column(Integer, nullable=False, default=0)
    o_lns = relationship("OrderLine", backref='order', lazy='dynamic')


class OrderLine(Base):
    __tablename__ = 'order_line'
    id = Column(Integer, primary_key=True)
    delivery_d = Column(String, nullable=True)
    item_id = Column(Integer, ForeignKey('item.id'), index=True)
    amount = Column(Integer, nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), index=True)


class History(Base):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True)
    date = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    data = Column(String, nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), index=True)
