"""Round 4: race the normalized four-way join against the denormalized report table.

Run with:  uv run python Module05/race.py
Needs Module05/normalize.db (setup.sql, then decompose.sql). Builds report_jobpart (Round 4)
and, for the optional "make the join hurt" try, report_wide + vendor + site_dim.
"""
import sqlite3, statistics, time
from pathlib import Path

DB = Path(__file__).with_name("normalize.db")
RUNS = 5

REPORT = """
DROP TABLE IF EXISTS report_jobpart;
CREATE TABLE report_jobpart AS
SELECT j.job_id, m.machine_id, m.site, j.technician, jp.part_no,
       p.part_price, j.done_on
FROM job j
JOIN machine m  ON m.machine_id = j.machine_id
JOIN job_part jp ON jp.job_id = j.job_id
JOIN part p     ON p.part_no = jp.part_no;
CREATE INDEX ix_report_machine ON report_jobpart(machine_id);
"""
A = """SELECT m.machine_id, m.site, j.technician, SUM(p.part_price) AS cost
FROM job j
JOIN machine m   ON m.machine_id = j.machine_id
JOIN job_part jp ON jp.job_id = j.job_id
JOIN part p      ON p.part_no = jp.part_no
WHERE j.done_on >= date('2026-03-01')
GROUP BY m.machine_id, j.technician"""
B = """SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM report_jobpart
WHERE done_on >= date('2026-03-01')
GROUP BY machine_id, technician"""

WIDE = """
DROP TABLE IF EXISTS vendor;
DROP TABLE IF EXISTS site_dim;
DROP TABLE IF EXISTS report_wide;
CREATE TABLE vendor(part_no TEXT PRIMARY KEY, vendor TEXT NOT NULL, country TEXT NOT NULL);
INSERT INTO vendor
SELECT part_no, 'vendor-' || (rowid % 12),
       CASE rowid % 3 WHEN 0 THEN 'DE' WHEN 1 THEN 'CN' ELSE 'US' END
FROM part;
CREATE TABLE site_dim(site TEXT PRIMARY KEY, region TEXT NOT NULL, manager TEXT NOT NULL);
INSERT INTO site_dim
SELECT site, 'region-' || (row_number() OVER () % 5), 'mgr-' || row_number() OVER ()
FROM (SELECT DISTINCT site FROM machine);
CREATE TABLE report_wide AS
SELECT j.job_id, m.machine_id, m.site, sd.region, j.technician, jp.part_no,
       p.part_price, v.vendor, j.done_on
FROM job j
JOIN machine m   ON m.machine_id = j.machine_id
JOIN site_dim sd ON sd.site = m.site
JOIN job_part jp ON jp.job_id = j.job_id
JOIN part p      ON p.part_no = jp.part_no
JOIN vendor v    ON v.part_no = p.part_no;
"""
A6 = """SELECT m.machine_id, m.site, sd.region, j.technician, v.vendor, SUM(p.part_price) AS cost
FROM job j
JOIN machine m   ON m.machine_id = j.machine_id
JOIN site_dim sd ON sd.site = m.site
JOIN job_part jp ON jp.job_id = j.job_id
JOIN part p      ON p.part_no = jp.part_no
JOIN vendor v    ON v.part_no = p.part_no
WHERE j.done_on >= date('2026-03-01')
GROUP BY m.machine_id, m.site, sd.region, j.technician, v.vendor"""
B6 = """SELECT machine_id, site, region, technician, vendor, SUM(part_price) AS cost
FROM report_wide
WHERE done_on >= date('2026-03-01')
GROUP BY machine_id, site, region, technician, vendor"""


def plan(sql):
    return "\n".join("    " + row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql))


def race(queries):
    """Warm every query once, then alternate them RUNS times; return the median ms of each."""
    for sql in queries.values():
        conn.execute(sql).fetchall()
    times = {name: [] for name in queries}
    for _ in range(RUNS):
        for name, sql in queries.items():
            start = time.perf_counter()
            conn.execute(sql).fetchall()
            times[name].append((time.perf_counter() - start) * 1000)
    return {name: statistics.median(t) for name, t in times.items()}


def same_result(q1, q2):
    diff = conn.execute(f"SELECT COUNT(*) FROM (SELECT * FROM ({q1}) EXCEPT SELECT * FROM ({q2}))").fetchone()[0]
    rows, total = conn.execute(f"SELECT COUNT(*), SUM(cost) FROM ({q1})").fetchone()
    return diff == 0, rows, total


# no statement cache: a cached EXPLAIN QUERY PLAN kept showing the dropped index (a stale plan)
conn = sqlite3.connect(DB, cached_statements=0)
conn.executescript(REPORT)
print(f"SQLite {sqlite3.sqlite_version}; warm cache; median of {RUNS} alternating runs\n")

print("== Round 4: A (normalized, 4 tables) vs B (report_jobpart, 1 table, with ix_report_machine)")
ok, rows, total = same_result(A, B)
print(f"  same answer: {ok}  ({rows} rows, total cost {total})")
print("  plan A:\n" + plan(A))
print("  plan B:\n" + plan(B))
t = race({"A": A, "B": B})
print(f"  A {t['A']:.1f} ms   B {t['B']:.1f} ms\n")

print("== Round 5 note: B again, after DROP INDEX ix_report_machine")
conn.execute("DROP INDEX ix_report_machine")
print("  plan B:\n" + plan(B))
t2 = race({"A": A, "B": B})
print(f"  A {t2['A']:.1f} ms   B (no index) {t2['B']:.1f} ms")
conn.execute("CREATE INDEX ix_report_machine ON report_jobpart(machine_id)")
print("  (index restored)\n")

print("== Optional: make the join hurt - six-way join vs report_wide")
conn.executescript(WIDE)
ok, rows, total = same_result(A6, B6)
print(f"  same answer: {ok}  ({rows} rows, total cost {total}; workbook says 3,500 rows and 722,610.0)")
print("  plan A6:\n" + plan(A6))
print("  plan B6:\n" + plan(B6))
t3 = race({"A6": A6, "B6": B6})
print(f"  A6 {t3['A6']:.1f} ms   B6 {t3['B6']:.1f} ms")
conn.close()
