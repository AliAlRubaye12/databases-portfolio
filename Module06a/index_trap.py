# Module06a/index_trap.py — run with:  uv run python Module06a/index_trap.py
"""After race.py adds ix_history_done_on, SQLite picks it for the dashboard too.
Every row matches done_on >= '2026-01-01', so the index cannot skip anything. Does it hurt?"""
import sqlite3, statistics, time
from pathlib import Path

RUNS = 3
DASH = """SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM report_history{hint} WHERE done_on >= '2026-01-01'
GROUP BY machine_id, site, technician"""

con = sqlite3.connect(Path(__file__).with_name("history.db"), cached_statements=0)
con.execute("DROP TABLE IF EXISTS sqlite_stat1")       # start without planner statistics


def measure(label, hint):
    sql = DASH.format(hint=hint)
    plan = " / ".join(r[3] for r in con.execute("EXPLAIN QUERY PLAN " + sql))
    con.execute(sql).fetchall()                         # warm-up
    times = []
    for _ in range(RUNS):
        t0 = time.perf_counter()
        con.execute(sql).fetchall()
        times.append((time.perf_counter() - t0) * 1000)
    print(f"{label:28s} {statistics.median(times):8.1f} ms   {plan}")


measure("planner's choice", "")
measure("NOT INDEXED (full scan)", " NOT INDEXED")
con.execute("ANALYZE")                                  # give the planner statistics
con.commit()
measure("planner's choice + ANALYZE", "")
