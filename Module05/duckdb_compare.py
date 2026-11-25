"""Round 7 stretcher: the same dashboard in DuckDB (columnar) — does it still need the report table?

Run with:  uv run python Module05/duckdb_compare.py
Copies the tables out of Module05/normalize.db via temporary CSV files into an in-memory DuckDB.
"""
import csv, sqlite3, statistics, tempfile, time
from pathlib import Path

import duckdb

DB = Path(__file__).with_name("normalize.db")
TABLES = ["machine", "part", "job", "job_part", "report_jobpart"]
RUNS = 5

# DuckDB has no date('...') function; a DATE literal is the equivalent
A = """SELECT m.machine_id, m.site, j.technician, SUM(p.part_price) AS cost
FROM job j
JOIN machine m   ON m.machine_id = j.machine_id
JOIN job_part jp ON jp.job_id = j.job_id
JOIN part p      ON p.part_no = jp.part_no
WHERE j.done_on >= DATE '2026-03-01'
GROUP BY m.machine_id, m.site, j.technician"""
B = """SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM report_jobpart
WHERE done_on >= DATE '2026-03-01'
GROUP BY machine_id, site, technician"""


def median_ms(con, sql):
    con.execute(sql).fetchall()                       # warm-up
    times = []
    for _ in range(RUNS):
        start = time.perf_counter()
        con.execute(sql).fetchall()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.median(times)


src = sqlite3.connect(DB)
duck = duckdb.connect()
with tempfile.TemporaryDirectory() as tmp:
    for table in TABLES:
        cur = src.execute(f"SELECT * FROM {table}")
        path = Path(tmp) / f"{table}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([d[0] for d in cur.description])
            w.writerows(cur)
        duck.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv('{path.as_posix()}')")
src.close()

print(f"DuckDB {duckdb.__version__}, in memory; warm cache; median of {RUNS} runs")
rows_a, total_a = duck.execute(f"SELECT COUNT(*), SUM(cost) FROM ({A})").fetchone()
rows_b, total_b = duck.execute(f"SELECT COUNT(*), SUM(cost) FROM ({B})").fetchone()
print(f"  A: {rows_a} rows, total {total_a}   B: {rows_b} rows, total {total_b}")
print(f"  A (normalized, 4-way join)   {median_ms(duck, A):7.1f} ms")
print(f"  B (report_jobpart, 1 table)  {median_ms(duck, B):7.1f} ms")
