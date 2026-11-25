"""Replay-safe ingest: load a CSV of readings with UPSERT, so running it twice adds nothing.

Run with:  uv run python Module04/ingest.py [csv]   (default: Module04/readings.csv)
Needs Module04/edge.db with ux_reading_sensor_ts (setup.sql, then task2.sql).
"""
import csv, sqlite3, sys
from pathlib import Path

here = Path(__file__).parent
csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "readings.csv"

UPSERT = """
    INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (?, ?, ?, ?)
    ON CONFLICT(sensor_id, ts) DO UPDATE SET value = excluded.value, interval_s = excluded.interval_s
"""

conn = sqlite3.connect(here / "edge.db")
conn.execute("PRAGMA foreign_keys = ON")             # every connection must switch it on again
before = conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0]

with csv_path.open(newline="") as f:
    rows = [(int(r["sensor_id"]), r["ts"], float(r["value"]), int(r["interval_s"]))
            for r in csv.DictReader(f)]
with conn:                                           # one transaction: all rows or none
    conn.executemany(UPSERT, rows)

after = conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0]
print(f"{len(rows)} CSV rows -> reading table {before} -> {after} rows")
conn.close()
