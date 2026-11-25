# Module06a/to_parquet.py — run with:  uv run python Module06a/to_parquet.py
"""200k CSV -> 2M-row Parquet. DuckDB does the expansion, no database server involved."""
import sqlite3
from pathlib import Path

import duckdb

here = Path(__file__).parent
csv_path = here / "report_jobpart.csv"
parquet = here / "report_history.parquet"

con = duckdb.connect()          # in-process, embedded — nothing to start
con.execute(f"""
    COPY (
      SELECT r.job_id + k * 1000000 AS job_id, r.machine_id, r.site,
             r.technician, r.part_no, r.part_price,
             CAST(r.done_on AS DATE) + CAST(k * 91 AS INTEGER) AS done_on
      FROM read_csv_auto('{csv_path.as_posix()}', header = true, encoding = 'utf-8') r,
           range(0, 10) t(k)
    ) TO '{parquet.as_posix()}' (FORMAT parquet)
""")

pq = f"read_parquet('{parquet.as_posix()}')"
print("parquet rows:", con.execute(f"SELECT COUNT(*) FROM {pq}").fetchone()[0])
print("parquet MB  :", round(parquet.stat().st_size / 1e6, 2))

# both sides must agree before anything is timed
d_rows, d_sum, d_min, d_max = con.execute(
    f"SELECT COUNT(*), ROUND(SUM(part_price), 2), MIN(done_on), MAX(done_on) FROM {pq}").fetchone()
sq = sqlite3.connect(here / "history.db")
s_rows, s_sum, s_min, s_max = sq.execute(
    "SELECT COUNT(*), ROUND(SUM(part_price), 2), MIN(done_on), MAX(done_on) FROM report_history").fetchone()
print(f"parquet : rows {d_rows}, sum {d_sum}, dates {d_min} .. {d_max}")
print(f"sqlite  : rows {s_rows}, sum {s_sum}, dates {s_min} .. {s_max}")
print("identical:", (d_rows, d_sum, str(d_min), str(d_max)) == (s_rows, s_sum, s_min, s_max))
print(f"sizes   : history.db {(here / 'history.db').stat().st_size / 1e6:.1f} MB, "
      f"parquet {parquet.stat().st_size / 1e6:.2f} MB")
