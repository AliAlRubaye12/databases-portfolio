# Module06a/refresh.py — run with:  uv run python Module06a/refresh.py [--check | --check-only]
"""Rebuild report_history.parquet from history.db, and with --check prove the copy matches.

--check-only compares the existing Parquet without rebuilding it — that is how a stale copy is detected.
Prints one line: rows, checksum, Parquet size, elapsed ms. Exits with status 1 on a mismatch.
"""
import csv, os, sqlite3, sys, tempfile, time
from pathlib import Path

import duckdb

here = Path(__file__).parent
db = here / "history.db"
parquet = here / "report_history.parquet"
tmp_parquet = here / "report_history.parquet.tmp"
COLUMNS = ("{'job_id': 'BIGINT', 'machine_id': 'VARCHAR', 'site': 'VARCHAR', 'technician': 'VARCHAR', "
           "'part_no': 'VARCHAR', 'part_price': 'DOUBLE', 'done_on': 'DATE'}")


def rebuild(src, duck):
    """Export the operational table, write the Parquet to a temp file, then swap it in."""
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "report_history.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["job_id", "machine_id", "site", "technician", "part_no", "part_price", "done_on"])
            w.writerows(src.execute("SELECT * FROM report_history"))
        duck.execute(f"""COPY (SELECT * FROM read_csv('{csv_path.as_posix()}', header = true, columns = {COLUMNS}))
                         TO '{tmp_parquet.as_posix()}' (FORMAT parquet)""")
    os.replace(tmp_parquet, parquet)          # a crash never leaves a half-written report


t0 = time.perf_counter()
src = sqlite3.connect(db)
duck = duckdb.connect()
if "--check-only" not in sys.argv:
    rebuild(src, duck)
elapsed = (time.perf_counter() - t0) * 1000

p_rows, p_sum = duck.execute(
    f"SELECT COUNT(*), ROUND(SUM(part_price), 2) FROM read_parquet('{parquet.as_posix()}')").fetchone()
print(f"rows {p_rows:,}  checksum SUM(part_price) {p_sum}  parquet {parquet.stat().st_size / 1e6:.2f} MB  "
      f"elapsed {elapsed:,.0f} ms")

if "--check" in sys.argv or "--check-only" in sys.argv:
    s_rows, s_sum = src.execute("SELECT COUNT(*), ROUND(SUM(part_price), 2) FROM report_history").fetchone()
    print(f"check: sqlite rows {s_rows:,} sum {s_sum} | parquet rows {p_rows:,} sum {p_sum}")
    if (s_rows, s_sum) != (p_rows, p_sum):
        print("check: MISMATCH")
        sys.exit(1)
    print("check: OK")
