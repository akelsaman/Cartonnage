import sys, os, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ake_cartonnage import Record, Database, SQLite
from settings import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=True, autocommit=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    db = SQLite(conn)
    Record.database__ = db
    return db


class Warehouse(Record): pass
class District(Record): pass
class Customer(Record): pass
class Item(Record): pass
class Stock(Record): pass
class Orders(Record): pass
class Order_line(Record): pass
class History(Record): pass
