# Module06a/race.py — run with:  uv run python Module06a/race.py
"""Same queries, two engines, interleaved, median of RUNS runs — and a check that the answers match."""
import sqlite3
import statistics
import time
from pathlib import Path

import duckdb

RUNS = 5        # odd on purpose: the median is then a real run

here = Path(__file__).parent
sq = sqlite3.connect(here / "history.db")
duck = duckdb.connect()
pq = (here / "report_history.parquet").as_posix()

DASHBOARD = """SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM {src} WHERE done_on >= '2026-01-01'
GROUP BY machine_id, site, technician"""

# the workbook's monthly query: DuckDB argument order strftime(date, format)
MONTHLY_WORKBOOK = """SELECT strftime(done_on, '%Y-%m') AS month, machine_id,
       COUNT(*) AS jobs, SUM(part_price) AS cost
FROM {src} GROUP BY month, machine_id ORDER BY month, machine_id"""
# SQLite needs strftime(format, date) — same question, engine-specific spelling
MONTHLY_SQLITE = """SELECT strftime('%Y-%m', done_on) AS month, machine_id,
       COUNT(*) AS jobs, SUM(part_price) AS cost
FROM {src} GROUP BY month, machine_id ORDER BY month, machine_id"""
MONTHLY_TRUNC = """SELECT strftime(date_trunc('month', done_on), '%Y-%m') AS month, machine_id,
       COUNT(*) AS jobs, SUM(part_price) AS cost
FROM {src} GROUP BY month, machine_id ORDER BY month, machine_id"""

ONE_DAY = """SELECT machine_id, SUM(part_price) AS cost
FROM {src} WHERE done_on = '2026-02-14' GROUP BY machine_id"""


def timed_ms(fn):
    t0 = time.perf_counter()
    fn()
    return (time.perf_counter() - t0) * 1000


def spread(times):
    return f"{min(times):.1f}-{max(times):.1f}"


def canon(rows):
    return sorted(tuple(round(v, 2) if isinstance(v, float) else str(v) for v in r) for r in rows)


def race(name, sqlite_sql, duck_sql):
    run_sqlite = lambda: sq.execute(sqlite_sql.format(src="report_history")).fetchall()
    run_duckdb = lambda: duck.execute(duck_sql.format(src=f"read_parquet('{pq}')")).fetchall()
    a, b = run_sqlite(), run_duckdb()          # warm-up, and the answers to compare
    sqlite_times, duckdb_times = [], []
    for _ in range(RUNS):                       # interleaved: alternate the engines
        sqlite_times.append(timed_ms(run_sqlite))
        duckdb_times.append(timed_ms(run_duckdb))
    s, d = statistics.median(sqlite_times), statistics.median(duckdb_times)
    same = canon(a) == canon(b)
    print(f"{name:22s} sqlite {s:7.1f} ms [{spread(sqlite_times)}]   duckdb {d:6.1f} ms "
          f"[{spread(duckdb_times)}]   {s / d:6.1f}x   rows {len(a)}/{len(b)}   same answer: {same}")


print(f"SQLite {sqlite3.sqlite_version} on history.db vs DuckDB {duckdb.__version__} on Parquet; "
      f"warm-up + median of {RUNS} interleaved runs\n")
race("dashboard", DASHBOARD, DASHBOARD)
race("monthly (workbook SQL)", MONTHLY_WORKBOOK, MONTHLY_WORKBOOK)
race("monthly (fixed SQLite)", MONTHLY_SQLITE, MONTHLY_WORKBOOK)
race("monthly (date_trunc)", MONTHLY_SQLITE, MONTHLY_TRUNC)
race("one day, no index", ONE_DAY, ONE_DAY)

sq.execute("CREATE INDEX IF NOT EXISTS ix_history_done_on ON report_history(done_on)")
plan = " / ".join(r[3] for r in sq.execute("EXPLAIN QUERY PLAN " + ONE_DAY.format(src="report_history")))
print(f"\n+ CREATE INDEX ix_history_done_on   (SQLite plan: {plan})")
race("one day, with index", ONE_DAY, ONE_DAY)
