"""Task 3: what does the alarm trigger cost? Time 10,000 inserts with and without it.

Run with:  uv run python Module04/trigger_cost.py
Uses a throwaway database file next to this script (bench.db, ignored by Git).
"""
import random, sqlite3, statistics, time
from pathlib import Path

here = Path(__file__).parent
SETUP = (here / "setup.sql").read_text(encoding="utf-8")
TRIGGER = """
CREATE TRIGGER trg_vib_alarm AFTER INSERT ON reading FOR EACH ROW
WHEN NEW.value > 2.0 AND (SELECT metric FROM sensor WHERE sensor_id = NEW.sensor_id) = 'vib_rms'
BEGIN
    INSERT INTO alarm(sensor_id, ts, value, reason)
    VALUES (NEW.sensor_id, NEW.ts, NEW.value, 'vibration over 2.0 mm/s');
END;
"""
ALARM = """CREATE TABLE alarm(alarm_id INTEGER PRIMARY KEY, sensor_id INTEGER NOT NULL REFERENCES sensor(sensor_id),
                              ts TEXT NOT NULL, value REAL NOT NULL, reason TEXT NOT NULL) STRICT;"""
N, RUNS = 10_000, 5

random.seed(4)
# one vibration sensor; about 14 % of the values (2.0..2.2 out of 0.8..2.2) are above the alarm threshold
rows = [(2, f"2026-03-02 {i // 3600:02d}:{i // 60 % 60:02d}:{i % 60:02d}",
         round(random.uniform(0.8, 2.2), 3), 1) for i in range(N)]


def one_run(with_trigger: bool) -> tuple[float, int]:
    db = here / "bench.db"
    db.unlink(missing_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript(SETUP + ALARM + (TRIGGER if with_trigger else ""))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executemany("INSERT INTO sensor VALUES (?, ?, ?, ?)",
                     [(1, "cnc-01", "temp_c", "degC"), (2, "cnc-01", "vib_rms", "mm/s")])
    conn.commit()
    start = time.perf_counter()
    with conn:
        conn.executemany("INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (?, ?, ?, ?)", rows)
    ms = (time.perf_counter() - start) * 1000
    alarms = conn.execute("SELECT COUNT(*) FROM alarm").fetchone()[0]
    conn.close()
    db.unlink()
    return ms, alarms


print(f"SQLite {sqlite3.sqlite_version}: {N:,} inserts in one transaction, median of {RUNS} runs")
results = {}
for label, flag in (("without trigger", False), ("with alarm trigger", True)):
    runs = [one_run(flag) for _ in range(RUNS)]
    results[label] = statistics.median(ms for ms, _ in runs)
    print(f"  {label:20s} {results[label]:8.1f} ms   alarms written: {runs[0][1]}")
extra = results["with alarm trigger"] - results["without trigger"]
print(f"  trigger cost: +{extra:.1f} ms ({extra / results['without trigger']:+.0%}), "
      f"{extra * 1000 / N:.2f} µs per row")
