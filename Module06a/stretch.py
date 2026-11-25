# Module06a/stretch.py — run with:  uv run python Module06a/stretch.py
"""S2 (row-group statistics: unsorted vs sorted) and S3 (snappy vs zstd), measured."""
import statistics, time
from pathlib import Path

import duckdb

here = Path(__file__).parent
src = (here / "report_history.parquet").as_posix()
sorted_pq = (here / "sorted.parquet").as_posix()
zstd_pq = (here / "report_zstd.parquet").as_posix()
RUNS = 5
con = duckdb.connect()


def median_ms(sql):
    con.execute(sql).fetchall()
    times = []
    for _ in range(RUNS):
        t0 = time.perf_counter()
        con.execute(sql).fetchall()
        times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times)


def groups(path):
    return con.execute(f"""SELECT row_group_id, stats_min, stats_max FROM parquet_metadata('{path}')
        WHERE path_in_schema = 'done_on' ORDER BY row_group_id""").fetchall()


print("== S2: row-group statistics for done_on")
con.execute(f"COPY (SELECT * FROM read_parquet('{src}') ORDER BY done_on) TO '{sorted_pq}' (FORMAT parquet)")
for name, path in (("unsorted", src), ("sorted", sorted_pq)):
    g = groups(path)
    print(f"  {name:8s} {len(g)} row groups; first three: " + "; ".join(f"{lo} .. {hi}" for _, lo, hi in g[:3]))
ONE_MONTH = "SELECT SUM(part_price) FROM read_parquet('{p}') WHERE done_on >= DATE '2027-03-01' AND done_on < DATE '2027-04-01'"
for name, path in (("unsorted", src), ("sorted", sorted_pq)):
    plan = con.execute("EXPLAIN ANALYZE " + ONE_MONTH.format(p=path)).fetchall()[0][1]
    scanned = next(line.strip(" │") for line in plan.splitlines() if "Row Groups Scanned" in line)
    print(f"  one-month query, {name:8s} {median_ms(ONE_MONTH.format(p=path)):6.2f} ms   {scanned.strip()}")

print("\n== S3: compression")
con.execute(f"COPY (SELECT * FROM read_parquet('{src}')) TO '{zstd_pq}' (FORMAT parquet, COMPRESSION zstd)")
DASH = "SELECT machine_id, site, technician, SUM(part_price) FROM read_parquet('{p}') GROUP BY ALL"
for name, path in (("snappy (default)", src), ("zstd", zstd_pq)):
    size = Path(path).stat().st_size / 1e6
    print(f"  {name:16s} {size:5.2f} MB   dashboard {median_ms(DASH.format(p=path)):6.1f} ms")
