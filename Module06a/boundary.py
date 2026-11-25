# Module06a/boundary.py — run with:  uv run python Module06a/boundary.py
"""1,000 single-row writes and lookups: the workload DuckDB is not built for."""
import sqlite3
import statistics
import time

import duckdb

N = 1_000
RUNS = 5
rows = [(i, f"k{i}", i * 1.5) for i in range(N)]


def run_sqlite(batched):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE s(id INTEGER PRIMARY KEY, k TEXT, v REAL)")
    t0 = time.perf_counter()
    if batched:
        con.executemany("INSERT INTO s VALUES (?, ?, ?)", rows)
    else:
        for r in rows:
            con.execute("INSERT INTO s VALUES (?, ?, ?)", r)
    con.commit()
    insert = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    for i in range(N):
        con.execute("SELECT v FROM s WHERE id = ?", (i,)).fetchone()
    return insert, (time.perf_counter() - t0) * 1000


def run_duckdb(batched):
    con = duckdb.connect()
    con.execute("CREATE TABLE s(id INTEGER PRIMARY KEY, k TEXT, v DOUBLE)")
    t0 = time.perf_counter()
    if batched:
        con.executemany("INSERT INTO s VALUES (?, ?, ?)", rows)
    else:
        for r in rows:
            con.execute("INSERT INTO s VALUES (?, ?, ?)", r)
    insert = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    for i in range(N):
        con.execute("SELECT v FROM s WHERE id = ?", (i,)).fetchone()
    return insert, (time.perf_counter() - t0) * 1000


def median_pair(fn, batched):
    runs = [fn(batched) for _ in range(RUNS)]
    return statistics.median(r[0] for r in runs), statistics.median(r[1] for r in runs)


print(f"{N:,} single-row statements, median of {RUNS} runs")
for label, batched in (("one by one", False), ("executemany", True)):
    si, sl = median_pair(run_sqlite, batched)
    di, dl = median_pair(run_duckdb, batched)
    print(f"  inserts ({label:11s}) sqlite {si:8.1f} ms | duckdb {di:8.1f} ms | {di / si:6.0f}x")
    if not batched:
        print(f"  lookups (by id)        sqlite {sl:8.1f} ms | duckdb {dl:8.1f} ms | {dl / sl:6.0f}x")
