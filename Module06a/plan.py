# Module06a/plan.py — run with:  uv run python Module06a/plan.py
"""The DuckDB physical plan (EXPLAIN ANALYZE runs the query) next to SQLite's access plan."""
import sqlite3
from pathlib import Path

import duckdb

here = Path(__file__).parent
pq = (here / "report_history.parquet").as_posix()

con = duckdb.connect()
for title, cols in (("4 columns", "machine_id, site, technician, SUM(part_price) AS cost"),
                    ("SELECT * (all 7 columns)", "*")):
    group = "GROUP BY machine_id, site, technician" if cols != "*" else ""
    plan = con.execute(f"EXPLAIN ANALYZE SELECT {cols} FROM read_parquet('{pq}') {group}").fetchall()[0][1]
    print(f"===== DuckDB EXPLAIN ANALYZE — {title}\n{plan}\n")

sq = sqlite3.connect(here / "history.db")
print("===== SQLite EXPLAIN QUERY PLAN — dashboard")
for row in sq.execute("""EXPLAIN QUERY PLAN
    SELECT machine_id, site, technician, SUM(part_price) AS cost
    FROM report_history WHERE done_on >= '2026-01-01'
    GROUP BY machine_id, site, technician"""):
    print("  ", row[3])
