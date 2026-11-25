# Module 4 — Data Integrity, Constraints & Edge Triggers

Course workbook: [Module 4](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/04-integrity-constraints-and-triggers.md) ·
back to [my portfolio](../README.md) · previous: [Module 3](../Module03/README.md)

## Learning Goals

<a id="lg1"></a>
### LG1 — `constraints`

Create tables with the full constraint toolkit: `NOT NULL`, `UNIQUE`, `CHECK`, `PRIMARY KEY`, `FOREIGN KEY`, and `STRICT` typing.

**Evidence:** [Task A — acceptance test](integrity-notes.md#task-a--the-acceptance-test), [Task 1](#task-1)

<a id="lg2"></a>
### LG2 — `generated`

Use **generated columns** to derive values at the engine instead of in application code.

**Evidence:** [Task 1 — `energy_j`](#task-1)

<a id="lg3"></a>
### LG3 — `triggers`

Write **triggers** that enforce domain rules and maintain audit/rollup tables automatically.

**Evidence:** [Task 3](#task-3), [Task 5](#task-5)

<a id="lg4"></a>
### LG4 — `upsert`

Use **DML** correctly — including `UPSERT` (`ON CONFLICT`) for idempotent edge ingestion.

**Evidence:** [Task 2](#task-2)

<a id="lg5"></a>
### LG5 — `dcl`

Reason about **access control (DCL)**: who may read or write, and how that maps from server `GRANT`s to an embedded, local-first world.

**Evidence:** [Task 4](#task-4)

## Pod study (Tasks A–B)

See [integrity-notes.md](integrity-notes.md): the acceptance test with every error message, verified LLM answers,
and our proposed points. _(Task B — sharing with another pod — still to do.)_

## Setup

[`setup.sql`](setup.sql) builds `edge.db` (ignored by Git):

```bash
sqlite3 Module04/edge.db ".read Module04/setup.sql"
```

Every later script starts with `PRAGMA foreign_keys = ON;` — each `sqlite3` call is a **new connection**, and foreign keys are off again in every new one.

<a id="task-1"></a>
## Task 1 — Prove the constraints work

**Proves:** [LG1](#lg1), [LG2](#lg2)

Script: [`task1.sql`](task1.sql) · output: [`task1-results.txt`](task1-results.txt)

| statement | layer | exact error |
|---|---|---|
| temperature `9000` | domain (`CHECK`) | `CHECK constraint failed: value >= -273.15 AND value <= 5000` |
| `'hot'` into `value` | domain (`STRICT`) | `cannot store TEXT value in REAL column reading.value` |
| sensor `99` | referential (`FOREIGN KEY`) | `FOREIGN KEY constraint failed` |
| second `cnc-01` / `temp_c` sensor | entity (`UNIQUE`) | `UNIQUE constraint failed: sensor.machine_id, sensor.metric` |

**The generated column computes:**

| reading | value | interval_s | energy_j |
|---|---:|---:|---:|
| valid row | 41.5 | 1 | **41.5** |
| a 5-second reading | 42.0 | 5 | **210.0** |

Writing `energy_j` directly is refused: `cannot INSERT into generated column "energy_j"`.

**What silently breaks without the pragma:** a fresh connection reports `PRAGMA foreign_keys` = `0` and **accepts** the reading for sensor 99 — no error at all ([`fk-off.sql`](fk-off.sql), rolled back).

<a id="task-2"></a>
## Task 2 — Idempotent edge ingestion with UPSERT

**Proves:** [LG4](#lg4)

Script: [`task2.sql`](task2.sql) · output: [`task2-results.txt`](task2-results.txt)

```sql
CREATE UNIQUE INDEX ux_reading_sensor_ts ON reading(sensor_id, ts);

INSERT INTO reading(sensor_id, ts, value, interval_s)
VALUES (1,'2026-03-01 08:00:00', 41.7, 1)
ON CONFLICT(sensor_id, ts) DO UPDATE SET value = excluded.value;
```

The replay changed 41.5 → **41.7** and the row count for that key stayed **1**. The same insert without `ON CONFLICT` is rejected (`UNIQUE constraint failed`).

[`ingest.py`](ingest.py) loads [`readings.csv`](readings.csv) (10 rows, including 2 replays of the same key with a corrected value) with `executemany` and the same UPSERT, in one transaction:

```text
== ingest.py, run 1
10 CSV rows -> reading table 1 -> 9 rows
== ingest.py, run 2 (same file)
10 CSV rows -> reading table 9 -> 9 rows
```

**Run 2 added nothing**: 9 rows, 9 distinct `(sensor_id, ts)` keys. The later, corrected values in the file won (41.95 and 1.15).

<a id="task-3"></a>
## Task 3 — Triggers for alarms and audit

**Proves:** [LG3](#lg3)

Trigger DDL: [`task3.sql`](task3.sql) · output: [`task3-results.txt`](task3-results.txt)

**Alarm** — inserting a vibration of 2.7 mm/s:

| alarm_id | sensor_id | ts | value | reason |
|---|---|---|---|---|
| 1 | 2 | 2026-03-01 09:00:00 | 2.7 | vibration over 2.0 mm/s |

A *temperature* of 2.7 raises no alarm — the `WHEN` clause checks the metric.

**Audit** — `UPDATE reading SET value = 1.4 WHERE sensor_id = 2` wrote one row per reading:

| reading_id | old_value | new_value |
|---|---:|---:|
| 5 | 1.2 | 1.4 |
| 6 | 1.3 | 1.4 |
| 7 | 1.15 | 1.4 |
| 9 | **1.4** | **1.4** |
| 10 | 2.7 | 1.4 |

Reading 9 was already 1.4, but it is still audited: `AFTER UPDATE OF value` fires whenever the column is *set*, not only when it *changes*.
Adding `WHEN OLD.value IS NOT NEW.value` would skip those. (`changed_at` is in UTC — `datetime('now')` always is.)

**Trigger cost** — [`trigger_cost.py`](trigger_cost.py), 10,000 vibration readings in one transaction, median of 5 runs ([output](trigger-cost-results.txt)):

| | time | alarms written |
|---|---:|---:|
| without trigger | 21.2 ms | 0 |
| with alarm trigger | 34.7 ms | 1,439 |
| **cost** | **+13.5 ms (+64%)** — about 1.4 µs per row | |

The trigger checks *every* row (including a lookup in `sensor`), not just the 14% that raise an alarm. For an edge gateway writing a few readings per second this is nothing; for a bulk import of millions of rows it is worth switching off and checking afterwards.

<a id="task-4"></a>
## Task 4 — Access control without a server

**Proves:** [LG5](#lg5)

Windows version of the workbook's commands: [`access.ps1`](access.ps1) (read-only attribute instead of `chmod 444`) · output: [`access-results.txt`](access-results.txt)

| control | read | write (`DELETE FROM reading`) |
|---|---|---|
| view `machine_health` | `cnc-01 temp_c peak 42.1` / `cnc-01 vib_rms peak 1.4` | — |
| file read-only (`chmod 444` / read-only attribute) | ✅ 11 rows | ❌ `attempt to write a readonly database` |
| connection `file:…?mode=ro` | ✅ 11 rows | ❌ `attempt to write a readonly database` |
| `PRAGMA query_only = ON` | ✅ | ❌ `attempt to write a readonly database` |

After the demo, write access was restored and all 11 readings were still there.

**How it would differ with PostgreSQL, and why file permissions are enough here:**
On a PostgreSQL server, each person logs in as a user, and `GRANT SELECT ON machine_health TO reporter` gives access to the view only — per user, per table, even per column, checked by the server.
SQLite has no users: whoever can open the file can read all of it, so control moves to the file system, to read-only connections, and to views that tools are told to use.
That is fine at the edge, where one gateway owns the file and the only other readers are on the same machine.
It is **not** fine for a multi-tenant web app: there, many customers' data share one database, and every request must be limited to its own rows — that needs a server checking each user, which a file permission cannot do.

<a id="task-5"></a>
## Task 5 (stretcher) — Break your own alarm

**Proves:** [LG3](#lg3)

Script: [`task5.sql`](task5.sql) (scratch database) · output: [`task5-results.txt`](task5-results.txt)

1. **As a `BEFORE INSERT` trigger,** the alarm sees `reading_id = -1` — the row has no id yet (the real id was 1). The alarm can never point to its reading.
2. **If the row then fails a constraint** (`interval_s = 0`), the whole statement is rolled back — including the alarm the `BEFORE` trigger had written. No ghost alarms, but also no record of the bad attempt.
3. **A rule a `CHECK` cannot express:** "readings arrive in time order per sensor". A `BEFORE INSERT` trigger with `RAISE(ABORT, 'reading is older than the latest one for this sensor')` rejected a late reading.

**Why `AFTER` is the right default for the alarm:** it only runs once the row has passed every constraint and has its real id, so every alarm belongs to a reading that really exists.
`BEFORE` is the right place for *rejecting* rows, like the time-order rule.

## Reflection 4

[Reflection 4](../Reflections/ref04.md)
