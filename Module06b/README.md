# Module 6b — Polyglot Persistence & the Decision

Course workbook: [Module 6b](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/06b-polyglot-persistence.md) ·
back to [my portfolio](../README.md) · previous: [Module 6a](../Module06a/README.md)

## Learning Goals

<a id="lg1"></a>
### LG1 — `json`

Store **semi-structured data (JSON)** in SQLite and query it with `json_extract`/`json_each` and an **expression index**.

**Evidence:** [Task 2](#task-2)

<a id="lg2"></a>
### LG2 — `key-value`

Implement and evaluate a **key-value access pattern** against SQLite.

**Evidence:** [Key-value benchmark](#kv)

<a id="lg3"></a>
### LG3 — `acid-base-cap`

Explain **ACID vs. BASE** and the **CAP theorem** in terms of the systems you actually ran.

**Evidence:** [Task 1](#task-1), [ACID/BASE/CAP in my own systems](#acid)

<a id="lg4"></a>
### LG4 — `decide`

Choose an engine per workload and **defend the choice with a measurement**.

**Evidence:** [Task 3 — decision record](#task-3)

<a id="lg5"></a>
### LG5 — `server`

Say what changes — and what gets harder — when the same data lives on a **server**.

**Evidence:** [Task 1](#task-1)

<a id="task-1"></a>
## Task 1 — The boundary (SQLite two-writer fallback)

**Proves:** [LG3](#lg3), [LG5](#lg5)

The shared PostgreSQL server is only reachable in class, so this is the workbook's fallback: two connections on one SQLite file —
[`two_writers.py`](two_writers.py), output in [`two-writers-results.txt`](two-writers-results.txt).

| test | result |
|---|---|
| writer A holds `BEGIN IMMEDIATE`, writer B tries too | B: **`database is locked`** — one writer at a time |
| a reader while A has not committed | sees **0** — no half-finished work (isolation) |
| A commits, B retries | counter **2** — both increments kept |
| **lost update:** both read the counter in the app, both write `read + 1` | counter **2 → 3**, expected 4 — one increment lost |
| the fix: `SET parts_produced = parts_produced + 1` in the database | counter **3 → 5** — both kept |

**Three observations:**

- **Easier on a server:** many writers can work at the same time from different machines — in SQLite the second writer simply gets `database is locked`.
- **Harder on a server:** the lost update does *not* go away. A server serializes conflicting writes, but a read in the app followed by a write is still a race — the fix is the same as in SQLite: do the increment inside one SQL statement (or lock the row).
- **The failure mode a server adds:** the database becomes a separate thing that can be *down*. With SQLite there is no server to lose — if the program runs, the database runs.

_Server session in class (pgweb): <add what you saw when two browsers updated the same row, and when the server was stopped>_

<a id="task-2"></a>
## Task 2 — The shape: JSON in SQLite

**Proves:** [LG1](#lg1)

[`json_bench.py`](json_bench.py) — output in [`json-bench-results.txt`](json-bench-results.txt).

```text
-- index the path you filter on, then prove it
[(3, 0, 61, 'SEARCH device USING INDEX ix_device_vendor (<expr>=?)')]
-- now break it: the shorthand is a different expression
[(2, 0, 216, 'SCAN device')]
-- same result: 334 rows vs 334 rows
-- non-JSON refused: CHECK constraint failed: json_valid(meta)
```

**Why `->>` loses the index:** an expression index only matches the *exact* expression it was built on, and `meta ->> 'vendor'` is written differently from `json_extract(meta, '$.vendor')` — the result is the same, but SQLite does not see them as the same expression.

`json_each` turns one device's object into rows (`vendor`, `firmware`, `calibrated`), and `CHECK (json_valid(meta))` — the Module 4 constraint idea — refused `'{vendor: Siemens'`.

<a id="kv"></a>
### Key-value benchmark (homework)

**Proves:** [LG2](#lg2)

[`kv_compare.py`](kv_compare.py), 20,000 sessions — output in [`kv-compare-results.txt`](kv-compare-results.txt):

| | set 20,000 | get 20,000 |
|---|---:|---:|
| `shelve` | 12.7 s | 0.23 s |
| SQLite table `session(k PRIMARY KEY, v)` | **0.07 s** | 1.57 s |

**Orders of magnitude:** writes ≈ 10 s vs ≈ 0.1 s; reads ≈ 0.1 s vs ≈ 1 s.

**A surprise:** on Python 3.14, `shelve`'s backend is **`dbm.sqlite3`** — the "key-value store" is itself a SQLite file. So this is not two engines: shelve commits after **every** write (12.7 s), while the SQLite version writes all 20,000 in one transaction (0.07 s). The engine is the same; the access pattern decides the number.

- **What I would ship for dashboard sessions:** a SQLite table. Both are fast enough for a login (well under 1 ms per lookup), and the table can do something `shelve` cannot:
- **A query across sessions:** "how many sessions per filter?" took **11.6 ms** as one `GROUP BY` (5,000 per city filter). With `shelve` you would have to load and parse every value in Python.

<a id="task-3"></a>
## Task 3 — The decision record for Kortmann

**Proves:** [LG4](#lg4)

| Workload | Engine | Why | Evidence | Cost accepted | What breaks if stale / missing? |
|---|---|---|---|---|---|
| Month-end report over two years | Parquet + DuckDB | the 2M-row scan is two orders of magnitude faster, and the writer stays free | [6a](../Module06a/README.md#task-3): dashboard **3,178 ms → 21 ms** (149×), monthly 3.8 s → 63 ms; Parquet **2.4 MB** vs 113 MB | a nightly rebuild (≈8 s) and up to one day of staleness | the report misses the newest jobs; `refresh.py --check-only` detects a mismatch (but not two changes that cancel out) |
| Sensor / job ingest, every 30 s, crash must not lose rows | SQLite, `STRICT` + constraints + UPSERT | one writer next to the machines, no server to lose; the database itself refuses bad rows | [Module 4](../Module04/README.md): double ingest **9 → 9 rows**; 9,000 °C rejected by `CHECK`; [Module 1](../Module01/README.md#task-6): 172,800 readings in 10 MB, queries ≈ 0.1 s | one writer at a time; `PRAGMA foreign_keys = ON` on every connection | a missed reading is a gap in the history; replaying it later is safe thanks to the UPSERT |
| Vendor metadata that gains fields | SQLite JSON column, `json_valid` + expression index | new vendor fields need no migration, and the document stays next to the relational row | Task 2: `SEARCH … USING INDEX ix_device_vendor` vs `SCAN device`; non-JSON refused | no per-field types; the index only works for the exact expression | a missing field is `NULL` — queries must expect it |
| Dashboard session state | SQLite table `session(k PRIMARY KEY, v)` | a key lookup is fast enough, and sessions can still be counted and grouped | [kv benchmark](#kv): 20,000 sets **0.07 s**, gets 1.57 s (≈80 µs each); sessions per filter **11.6 ms** | another table in the same file; one writer at a time | a lost session means one user logs in again — harmless |
| *(optional)* Concurrent users on the network | SQLite until measured otherwise | the edge has one writer; the dashboards only read | Task 1: second writer gets `database is locked`; lost update 2 → 3 even with a lock | writes must be short; increments must be done in SQL | under many simultaneous writers, requests fail with `database is locked` — that is the measured reason to move to a server |

**If Kortmann could run only one engine:** **SQLite.** It already does the ingest, the metadata and the sessions with numbers to show for it.
**What breaks first** is the two-year report: 3.2 s on 2 million rows with the best plan, **7.4 s** once someone adds the "wrong" index — and it grows with every month of history. That is the one workload where a measurement (149×) already justifies a second engine.

**Defence with another pod:** _<the questions the other pod asked, and the one row we changed afterwards, with the reason>_

<a id="acid"></a>
## ACID, BASE, CAP — in the systems I actually ran

- **ACID** — SQLite in Task 1: the reader saw **0** while A's change was uncommitted (isolation); the double UPSERT ingest in Module 4 kept every row exactly once (atomicity + consistency).
- **BASE** — the Parquet copy in 6a is *eventually consistent* with SQLite: after one price changed, `--check-only` reported a mismatch until the next refresh.
- **CAP** — a partition only exists when data is distributed. SQLite on one machine has nothing to partition, so it can stay consistent *and* available. The Parquet copy is the closest thing here to an "AP" choice: always readable, possibly a day old.

## Project ticket

[project-ticket.md](project-ticket.md) — three candidate ideas for the final-project kickoff.

## Reflection 6b

[Reflection 6b](../Reflections/ref06b.md)
