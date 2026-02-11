#!/usr/bin/env python3
"""
TPC-C Benchmark: Cartonnage vs PonyORM vs SQLAlchemy
Runs each transaction type separately per ORM and reports transactions/minute.
"""

import os
import sys
import time
import multiprocessing
from random import randint
from multiprocessing import Process, Value

# Use 'fork' on macOS to avoid pickling issues with 'spawn'
if sys.platform == 'darwin':
    multiprocessing.set_start_method('fork', force=True)

from settings import (
    AMOUNT_OF_WAREHOUSES, AMOUNT_OF_PROCESSES,
    TEST_DURATION, PRINT_INTERVAL
)
from schema import create_db, DB_PATH

TRAN_NAMES = ['new_order', 'payment', 'order_status', 'delivery', 'stock_level']

# ─────────────────────────────────────────────────────────────────────────────
# Seed helper: creates orders so read/delivery/stock_level transactions work
# ─────────────────────────────────────────────────────────────────────────────

def seed_orders(n=200):
    """Seed orders via raw SQL (ORM-agnostic, avoids state leaks between ORMs)."""
    import sqlite3
    from random import randint, choice
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH, autocommit=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    districts = [r[0] for r in conn.execute("SELECT id FROM district").fetchall()]
    items = [r[0] for r in conn.execute("SELECT id FROM item").fetchall()]
    for i in range(n):
        w_id = (i % AMOUNT_OF_WAREHOUSES) + 1
        c_id = (i % (AMOUNT_OF_WAREHOUSES * 10)) + 1
        d_id = choice([d for d in districts if (d - 1) // 10 + 1 == w_id] or districts)
        ol_cnt = randint(1, 10)
        amount = randint(1, 10)
        now = datetime.now().isoformat()
        cur = conn.execute(
            "INSERT INTO orders (warehouse_id, district_id, ol_cnt, customer_id, entry_d, is_o_delivered) VALUES (?,?,?,?,?,0)",
            (w_id, d_id, ol_cnt, c_id, now)
        )
        order_id = cur.lastrowid
        for _ in range(ol_cnt):
            item_id = choice(items)
            conn.execute(
                "INSERT INTO order_line (order_id, item_id, amount) VALUES (?,?,?)",
                (order_id, item_id, amount)
            )
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# Worker functions (each runs in a subprocess)
# ─────────────────────────────────────────────────────────────────────────────

def _make_args(tran_idx):
    if tran_idx in (0, 1):
        return {'w_id': randint(1, AMOUNT_OF_WAREHOUSES), 'c_id': randint(1, AMOUNT_OF_WAREHOUSES * 10)}
    elif tran_idx == 2:
        return {'c_id': randint(1, AMOUNT_OF_WAREHOUSES * 10)}
    else:
        return {'w_id': randint(1, AMOUNT_OF_WAREHOUSES)}


def worker_cartonnage(cnt, run, tran_idx):
    from cartonnage_bench.models import init_db
    from cartonnage_bench import transactions as T
    init_db()
    fns = [T.new_order_tran, T.payment_tran, T.order_status_tran, T.delivery_tran, T.stock_level_tran]
    fn = fns[tran_idx]
    while run.value:
        try:
            if fn(**_make_args(tran_idx)):
                with cnt.get_lock():
                    cnt.value += 1
        except Exception:
            pass


def worker_pony(cnt, run, tran_idx):
    from pony_bench.models import init_db
    from pony_bench import transactions as T
    init_db()
    fns = [T.new_order_tran, T.payment_tran, T.order_status_tran, T.delivery_tran, T.stock_level_tran]
    fn = fns[tran_idx]
    while run.value:
        try:
            if fn(**_make_args(tran_idx)):
                with cnt.get_lock():
                    cnt.value += 1
        except Exception:
            pass


def worker_sqlalchemy(cnt, run, tran_idx):
    from sqlalchemy_bench import transactions as T
    fns = [T.new_order_tran, T.payment_tran, T.order_status_tran, T.delivery_tran, T.stock_level_tran]
    fn = fns[tran_idx]
    while run.value:
        try:
            if fn(**_make_args(tran_idx)):
                with cnt.get_lock():
                    cnt.value += 1
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark runner
# ─────────────────────────────────────────────────────────────────────────────

def run_benchmark(orm_name, worker_fn, tran_idx):
    label = f"{orm_name}/{TRAN_NAMES[tran_idx]}"
    print(f"\n>>> {label} | {TEST_DURATION}s | {AMOUNT_OF_PROCESSES} processes")

    cnt = Value('i', 0)
    run = Value('b', True)
    gl_start = time.time()

    processes = []
    for _ in range(AMOUNT_OF_PROCESSES):
        p = Process(target=worker_fn, args=(cnt, run, tran_idx))
        p.start()
        processes.append(p)

    # Controller in main process
    last_print = gl_start
    while True:
        time.sleep(0.5)
        now = time.time()
        if now - gl_start >= TEST_DURATION:
            run.value = False
            break
        if now - last_print >= PRINT_INTERVAL:
            tpm = cnt.value / (now - gl_start) * 60
            print(f"  [{label}] cumulative: {cnt.value} txns ({tpm:.0f} tpm)")
            last_print = now

    for p in processes:
        p.join(timeout=10)

    elapsed = time.time() - gl_start
    total = cnt.value
    tpm = total / elapsed * 60 if elapsed > 0 else 0
    print(f"  [{label}] FINAL: {total} txns in {elapsed:.1f}s = {tpm:.0f} tpm")
    return tpm


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("TPC-C Benchmark: Cartonnage vs PonyORM vs SQLAlchemy (SQLite)")
    print(f"Config: {AMOUNT_OF_WAREHOUSES} warehouses, {AMOUNT_OF_PROCESSES} processes, {TEST_DURATION}s per test")
    print("=" * 70)

    results = {}

    orms = [
        ('Cartonnage',  worker_cartonnage),
        ('PonyORM',     worker_pony),
        ('SQLAlchemy',  worker_sqlalchemy),
    ]

    for orm_name, worker_fn in orms:
        results[orm_name] = {}
        print(f"\n{'─' * 70}")
        print(f"  {orm_name}")
        print(f"{'─' * 70}")

        for tran_idx in range(5):
            # Fresh DB + seed for each test
            create_db()
            if tran_idx >= 1:  # payment, order_status, delivery, stock_level need orders
                seed_orders(200)

            tpm = run_benchmark(orm_name, worker_fn, tran_idx)
            results[orm_name][TRAN_NAMES[tran_idx]] = tpm

    # ─── Results Table ───
    print("\n")
    print("=" * 70)
    print("RESULTS (transactions per minute)")
    print("=" * 70)

    header = f"{'Transaction':<20}"
    for orm_name in results:
        header += f"{orm_name:>16}"
    print(header)
    print("─" * (20 + 16 * len(results)))

    totals = {orm: 0 for orm in results}
    for tran in TRAN_NAMES:
        row = f"{tran:<20}"
        for orm_name in results:
            val = results[orm_name].get(tran, 0)
            totals[orm_name] += val
            row += f"{val:>14.0f}  "
        print(row)

    print("─" * (20 + 16 * len(results)))
    row = f"{'AVERAGE':<20}"
    for orm_name in results:
        avg = totals[orm_name] / len(TRAN_NAMES)
        row += f"{avg:>14.0f}  "
    print(row)
    print()


if __name__ == '__main__':
    main()
