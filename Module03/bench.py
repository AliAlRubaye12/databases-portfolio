"""Task 2: index benchmark — plan and median time, one index at a time.

Run with:  uv run python Module03/bench.py
Needs Module03/warehouse.db (build it with setup.sql first). Leaves all three indexes in place.
"""
import sqlite3, statistics, time
from pathlib import Path

DB = Path(__file__).with_name("warehouse.db")
if not DB.exists():
    raise SystemExit(f"{DB} not found — run the Module 3 setup first")

QUERIES = {
    "dashboard": """
        SELECT c.city, COUNT(DISTINCT c.customer_id) AS customers, SUM(ol.qty * p.price) AS revenue
        FROM customer c
        JOIN orders o      ON o.customer_id = c.customer_id
        JOIN order_line ol ON ol.order_id = o.order_id
        JOIN product p     ON p.product_id = ol.product_id
        WHERE o.ordered_on >= '2025-01-01' AND o.ordered_on < '2026-01-01'
        GROUP BY c.city ORDER BY revenue DESC""",
    "single day": """
        SELECT o.order_id, o.ordered_on, c.name
        FROM orders o JOIN customer c ON c.customer_id = o.customer_id
        WHERE o.ordered_on = '2026-02-14'""",
    "single day, date()": """
        SELECT o.order_id, o.ordered_on, c.name
        FROM orders o JOIN customer c ON c.customer_id = o.customer_id
        WHERE date(o.ordered_on) = '2026-02-14'""",
    "one product": """
        SELECT SUM(qty) FROM order_line WHERE product_id = 42""",
}

# the dashboard is slow enough to time directly; the lookups need an amortized batch
REPEAT = {"dashboard": 1, "single day": 200, "single day, date()": 20, "one product": 20}
RUNS = 5

STEPS = [
    ("no index", None),
    ("+ ix_orders_ordered_on", "CREATE INDEX ix_orders_ordered_on ON orders(ordered_on)"),
    ("+ ix_orderline_order", "CREATE INDEX ix_orderline_order ON order_line(order_id)"),
    ("+ ix_orderline_product", "CREATE INDEX ix_orderline_product ON order_line(product_id)"),
]


def plan(conn, sql):
    return " / ".join(row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql))


def median_ms(conn, sql, repeat):
    conn.execute(sql).fetchall()                         # warm-up: the first run pays for the file cache
    times = []
    for _ in range(RUNS):
        start = time.perf_counter()
        for _ in range(repeat):
            conn.execute(sql).fetchall()
        times.append((time.perf_counter() - start) / repeat * 1000)
    return statistics.median(times)


conn = sqlite3.connect(DB)
for name in ("ix_orders_ordered_on", "ix_orderline_order", "ix_orderline_product"):
    conn.execute(f"DROP INDEX IF EXISTS {name}")
print(f"SQLite {sqlite3.sqlite_version}, median of {RUNS} runs, times in ms\n")

results = {}
for step, ddl in STEPS:
    if ddl:
        conn.execute(ddl)
        conn.execute("ANALYZE")                          # give the planner fresh statistics
    print(f"== {step}")
    for qname, sql in QUERIES.items():
        ms = median_ms(conn, sql, REPEAT[qname])
        results[(step, qname)] = ms
        print(f"  {qname:20s} {ms:9.3f} ms   {plan(conn, sql)}")
    print()

print("| query | " + " | ".join(step for step, _ in STEPS) + " |")
print("|---|" + "---:|" * len(STEPS))
for qname in QUERIES:
    print(f"| {qname} | " + " | ".join(f"{results[(step, qname)]:.3f}" for step, _ in STEPS) + " |")
conn.close()
