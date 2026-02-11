"""PonyORM transactions using ORM query builder (requires Python <= 3.13)."""

from random import randint, choice
from datetime import datetime
from pony.orm import db_session, select, desc
from settings import AMOUNT_OF_WAREHOUSES
from pony_bench.models import (
    db, Warehouse, District, Customer, Item, Stock, Order, OrderLine, History
)


@db_session
def new_order_tran(w_id, c_id):
    districts = select(d for d in District if d.warehouse.id == w_id)[:]
    district = choice(districts)
    ol_cnt = randint(1, 10)
    amount = randint(1, 10)
    now = datetime.now().isoformat()

    order = Order(
        warehouse=Warehouse[w_id], district=district,
        ol_cnt=ol_cnt, customer=Customer[c_id],
        entry_d=now, is_o_delivered=0
    )

    items_ids = []
    for _ in range(ol_cnt):
        item_id = randint(1, AMOUNT_OF_WAREHOUSES * 10)
        items_ids.append(item_id)
        OrderLine(order=order, item=Item[item_id], amount=amount)

    unique_ids = list(set(items_ids))
    stocks = select(s for s in Stock if s.warehouse.id == w_id and s.item.id in unique_ids)[:]
    for stock in stocks:
        count = items_ids.count(stock.item.id)
        stock.order_cnt += 1
        stock.quantity -= amount * count
    return True


@db_session
def payment_tran(w_id, c_id):
    h_amount = randint(10, 5000)
    now = datetime.now().isoformat()

    whouse = Warehouse[w_id]
    districts = select(d for d in District if d.warehouse == whouse)[:]
    district = choice(districts)
    customer = Customer[c_id]

    whouse.ytd += h_amount
    district.ytd += h_amount
    customer.balance -= h_amount
    customer.ytd_payment += h_amount
    customer.payment_cnt += 1

    History(date=now, amount=h_amount, data='new_payment', customer=customer)
    return True


@db_session
def order_status_tran(c_id):
    orders = select(o for o in Order if o.customer.id == c_id).order_by(desc(Order.id))[:1]
    if not orders:
        return False
    last_order = orders[0]
    _ = last_order.is_o_delivered
    for ol in last_order.o_lns:
        _ = {'delivery_d': ol.delivery_d, 'item_id': ol.item.id, 'amount': ol.amount}
    return True


@db_session
def delivery_tran(w_id):
    districts = select(d for d in District if d.warehouse.id == w_id).order_by(District.id)[:]
    customer_ids = []
    now = datetime.now().isoformat()

    for district in districts:
        orders = select(
            o for o in Order if o.district == district and o.is_o_delivered == 0
        ).order_by(Order.id)[:1]
        if not orders:
            return False
        order = orders[0]
        order.is_o_delivered = 1
        for ol in order.o_lns:
            ol.delivery_d = now
        customer_ids.append(order.customer.id)

    unique_cids = list(set(customer_ids))
    for cid in unique_cids:
        customer = Customer[cid]
        count = customer_ids.count(cid)
        customer.delivery_cnt += count
    return True


@db_session
def stock_level_tran(w_id):
    recent_orders = select(
        o for o in Order if o.warehouse.id == w_id
    ).order_by(desc(Order.id))[:20]
    items_stock = {}
    for order in recent_orders:
        for ol in order.o_lns:
            item = ol.item
            if item.name in items_stock:
                continue
            stock = select(
                s for s in Stock if s.warehouse.id == w_id and s.item == item
            ).first()
            if stock:
                items_stock[item.name] = stock.quantity
    return True
