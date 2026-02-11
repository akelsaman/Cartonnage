from random import randint, choice
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ake_cartonnage import Record
from settings import AMOUNT_OF_WAREHOUSES
from cartonnage_bench.models import (
    Warehouse, District, Customer, Item, Stock, Orders, Order_line, History
)


def _lastrowid():
    """Get lastrowid from the database cursor after an insert."""
    return Record.database__._Database__cursor.lastrowid


def new_order_tran(w_id, c_id):
    try:
        districts = District().where(District.warehouse_id == w_id).select()
        district = choice(list(districts.recordset.iterate()))
        ol_cnt = randint(1, 10)
        amount = randint(1, 10)

        order = Orders()
        order.data = {
            'warehouse_id': w_id, 'district_id': district.id,
            'ol_cnt': ol_cnt, 'customer_id': c_id,
            'entry_d': datetime.now().isoformat(), 'is_o_delivered': 0
        }
        order.insert()
        order_id = _lastrowid()

        items_ids = []
        for _ in range(ol_cnt):
            item_id = randint(1, AMOUNT_OF_WAREHOUSES * 10)
            items_ids.append(item_id)
            ol = Order_line()
            ol.data = {'order_id': order_id, 'item_id': item_id, 'amount': amount}
            ol.insert()

        unique_ids = list(set(items_ids))
        stocks = Stock().where(
            (Stock.warehouse_id == w_id) & (Stock.item_id.in_(unique_ids))
        ).select()
        for stock in stocks.recordset.iterate():
            count = items_ids.count(stock.item_id)
            Stock().value(id=stock.id).set(
                order_cnt=stock.order_cnt + 1,
                quantity=stock.quantity - amount * count
            ).update()

        Record.database__.commit()
        return True
    except Exception:
        Record.database__.rollback()
        return False


def payment_tran(w_id, c_id):
    try:
        whouse = Warehouse().value(id=w_id).select()
        districts = District().where(District.warehouse_id == w_id).select()
        district = choice(list(districts.recordset.iterate()))
        customer = Customer().value(id=c_id).select()
        h_amount = randint(10, 5000)

        Warehouse().value(id=w_id).set(ytd=whouse.ytd + h_amount).update()
        District().value(id=district.id).set(ytd=district.ytd + h_amount).update()
        Customer().value(id=c_id).set(
            balance=customer.balance - h_amount,
            ytd_payment=customer.ytd_payment + h_amount,
            payment_cnt=customer.payment_cnt + 1
        ).update()

        h = History()
        h.data = {
            'date': datetime.now().isoformat(),
            'amount': h_amount,
            'data': 'new_payment',
            'customer_id': c_id
        }
        h.insert()

        Record.database__.commit()
        return True
    except Exception:
        Record.database__.rollback()
        return False


def order_status_tran(c_id):
    try:
        q = Orders().where(Orders.customer_id == c_id)
        last_order = q.select(order_by='id DESC', limit=q.limit(1, 1))

        if not last_order.data:
            return False

        order_lines = Order_line().where(
            Order_line.order_id == last_order.id
        ).select()

        _ = last_order.is_o_delivered
        for ol in order_lines.recordset.iterate():
            _ = {'delivery_d': ol.delivery_d, 'item_id': ol.item_id, 'amount': ol.amount}
        return True
    except Exception:
        return False


def delivery_tran(w_id):
    try:
        districts = District().where(District.warehouse_id == w_id).select()
        customer_ids = []
        for district in districts.recordset.iterate():
            q = Orders().where(
                (Orders.district_id == district.id) & (Orders.is_o_delivered == 0)
            )
            order = q.select(order_by='id ASC', limit=q.limit(1, 1))
            if not order.data:
                Record.database__.rollback()
                return False
            Orders().value(id=order.id).set(is_o_delivered=1).update()

            ols = Order_line().where(Order_line.order_id == order.id).select()
            for ol in ols.recordset.iterate():
                Order_line().value(id=ol.id).set(delivery_d=datetime.now().isoformat()).update()
            customer_ids.append(order.customer_id)

        unique_cids = list(set(customer_ids))
        for cid in unique_cids:
            cust = Customer().value(id=cid).select()
            count = customer_ids.count(cid)
            Customer().value(id=cid).set(delivery_cnt=cust.delivery_cnt + count).update()

        Record.database__.commit()
        return True
    except Exception:
        Record.database__.rollback()
        return False


def stock_level_tran(w_id):
    try:
        q = Orders().where(Orders.warehouse_id == w_id)
        recent_orders = q.select(order_by='id DESC', limit=q.limit(1, 20))

        items_stock = {}
        for order in recent_orders.recordset.iterate():
            ols = Order_line().where(Order_line.order_id == order.id).select()
            for ol in ols.recordset.iterate():
                item = Item().value(id=ol.item_id).select()
                if item.name in items_stock:
                    continue
                stock = Stock().where(
                    (Stock.warehouse_id == w_id) & (Stock.item_id == ol.item_id)
                ).select()
                items_stock[item.name] = stock.quantity
        return True
    except Exception:
        return False
