"""Task 5 (stretcher): late orders per customer — GROUP BY vs correlated subquery vs window function.

Run with:  uv run python Module03/task5.py
Needs Module03/warehouse.db (setup.sql). Checks that the versions agree, then compares plans and timings.
"""
import sqlite3, statistics, time
from pathlib import Path

DB = Path(__file__).with_name("warehouse.db")
RUNS = 5

QUERIES = {
    "GROUP BY (workbook)": """
        SELECT c.customer_id, c.name, COUNT(*) AS late_orders
        FROM orders o
        JOIN customer c ON c.customer_id = o.customer_id
        WHERE o.status = 'late'
        GROUP BY c.customer_id, c.name
        ORDER BY late_orders DESC""",
    "correlated subquery": """
        SELECT customer_id, name, late_orders FROM (
            SELECT c.customer_id, c.name,
                   (SELECT COUNT(*) FROM orders o
                    WHERE o.customer_id = c.customer_id AND o.status = 'late') AS late_orders
            FROM customer c)
        WHERE late_orders > 0
        ORDER BY late_orders DESC""",
    "window function": """
        SELECT DISTINCT c.customer_id, c.name,
               COUNT(*) OVER (PARTITION BY c.customer_id) AS late_orders
        FROM orders o
        JOIN customer c ON c.customer_id = o.customer_id
        WHERE o.status = 'late'
        ORDER BY late_orders DESC""",
    "window, DISTINCT forgotten": """
        SELECT c.customer_id, c.name,
               COUNT(*) OVER (PARTITION BY c.customer_id) AS late_orders
        FROM orders o
        JOIN customer c ON c.customer_id = o.customer_id
        WHERE o.status = 'late'
        ORDER BY late_orders DESC""",
}

conn = sqlite3.connect(DB, cached_statements=0)
reference = sorted(conn.execute(QUERIES["GROUP BY (workbook)"]).fetchall())
print(f"SQLite {sqlite3.sqlite_version}; median of {RUNS} runs after one warm-up\n")
for name, sql in QUERIES.items():
    rows = conn.execute(sql).fetchall()
    times = []
    for _ in range(RUNS):
        t0 = time.perf_counter()
        conn.execute(sql).fetchall()
        times.append((time.perf_counter() - t0) * 1000)
    print(f"== {name}: {len(rows)} rows, same answer as GROUP BY: {sorted(rows) == reference}, "
          f"{statistics.median(times):.1f} ms")
    for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
        print("     ", row[3])

print("\n== the ranking itself: how many customers share the top count?")
print("  ", conn.execute("""SELECT late_orders, COUNT(*) AS customers FROM (
                 SELECT customer_id, COUNT(*) AS late_orders FROM orders WHERE status = 'late'
                 GROUP BY customer_id) GROUP BY late_orders""").fetchall())
print("== customers with no late order at all:",
      conn.execute("""SELECT COUNT(*) FROM customer c WHERE NOT EXISTS
                 (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.status = 'late')""").fetchone()[0])

# can an index rescue the correlated subquery? (dropped again, so Task 2's benchmark stays reproducible)
conn.execute("CREATE INDEX ix_tmp_orders_customer ON orders(customer_id, status)")
sql = QUERIES["correlated subquery"]
conn.execute(sql).fetchall()
times = []
for _ in range(RUNS):
    t0 = time.perf_counter()
    conn.execute(sql).fetchall()
    times.append((time.perf_counter() - t0) * 1000)
print(f"\n== correlated subquery + index on orders(customer_id, status): {statistics.median(times):.1f} ms")
for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
    print("     ", row[3])
conn.execute("DROP INDEX ix_tmp_orders_customer")
conn.close()
