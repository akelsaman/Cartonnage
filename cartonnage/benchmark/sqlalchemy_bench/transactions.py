from random import randint, choice
from datetime import datetime
from sqlalchemy import text
from settings import AMOUNT_OF_WAREHOUSES
from sqlalchemy_bench.models import (
    Session, Warehouse, District, Customer, Item, Stock,
    Order, OrderLine, History
)


def new_order_tran(w_id, c_id):
    session = Session()
    try:
        whouse = session.query(Warehouse).filter(Warehouse.id == w_id).first()
        district = choice(whouse.districts.all())
        customer = session.query(Customer).filter(Customer.id == c_id).first()
        ol_cnt = randint(1, 10)
        amount = randint(1, 10)

        order = Order(
            ol_cnt=ol_cnt,
            customer_id=customer.id,
            entry_d=datetime.now().isoformat(),
            warehouse=whouse,
            district=district
        )
        session.add(order)
        session.flush()

        items_ids = []
        for _ in range(ol_cnt):
            item = session.query(Item).filter(
                Item.id == randint(1, AMOUNT_OF_WAREHOUSES * 10)
            ).first()
            items_ids.append(item.id)
            session.add(OrderLine(item=item, amount=amount, order=order))

        stocks = session.query(Stock).filter(
            Stock.warehouse_id == whouse.id, Stock.item_id.in_(items_ids)
        ).order_by(text("id")).all()
        for stock in stocks:
            i_in_o = items_ids.count(stock.item_id)
            stock.order_cnt += 1
            stock.quantity -= amount * i_in_o

        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def payment_tran(w_id, c_id):
    session = Session()
    try:
        whouse = session.query(Warehouse).filter(Warehouse.id == w_id).first()
        district = choice(whouse.districts.all())
        customer = session.query(Customer).filter(Customer.id == c_id).first()
        h_amount = randint(10, 5000)

        whouse.ytd += h_amount
        district.ytd += h_amount
        customer.balance -= h_amount
        customer.ytd_payment += h_amount
        customer.payment_cnt += 1

        session.add(History(
            amount=h_amount,
            data='new_payment',
            date=datetime.now().isoformat(),
            customer=customer,
        ))
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def order_status_tran(c_id):
    session = Session()
    try:
        customer = session.query(Customer).filter(Customer.id == c_id).first()
        last_order = session.query(Order).filter(
            Order.customer == customer
        ).order_by(text("id desc")).first()
        if not last_order:
            return False
        _ = last_order.is_o_delivered
        for ol in last_order.o_lns:
            _ = {'delivery_d': ol.delivery_d, 'item_id': ol.item_id, 'amount': ol.amount}
        return True
    except Exception:
        return False
    finally:
        session.close()


def delivery_tran(w_id):
    session = Session()
    try:
        whouse = session.query(Warehouse).filter(Warehouse.id == w_id).first()
        districts = session.query(District).filter(
            District.warehouse == whouse
        ).order_by(text("id"))
        customers_id = []
        for district in districts:
            order = session.query(Order).filter(
                Order.district == district, Order.is_o_delivered == 0
            ).order_by(text("id")).first()
            if not order:
                session.commit()
                return False
            order.is_o_delivered = 1
            for o_l in order.o_lns:
                o_l.delivery_d = datetime.now().isoformat()
            customers_id.append(order.customer_id)

        customers = session.query(Customer).filter(
            Customer.id.in_(customers_id)
        ).order_by(text("id"))
        for customer in customers:
            count = customers_id.count(customer.id)
            customer.delivery_cnt += count
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def stock_level_tran(w_id):
    session = Session()
    try:
        whouse = session.query(Warehouse).filter(Warehouse.id == w_id).first()
        items_stock = {}
        orders = session.query(Order).filter(
            Order.warehouse == whouse
        ).order_by(text("id desc")).limit(20).all()
        for order in orders:
            for ol in order.o_lns:
                item = session.query(Item).filter(Item.id == ol.item_id).first()
                if item.name in items_stock:
                    continue
                stock = session.query(Stock).filter(
                    Stock.warehouse == whouse, Stock.item == item
                ).first()
                items_stock[item.name] = stock.quantity
        return True
    except Exception:
        return False
    finally:
        session.close()
