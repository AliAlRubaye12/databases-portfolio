# Module 5 — Normalization vs. Denormalization Benchmarking Studio

Course workbook: [Module 5](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/05-normalization-vs-denormalization.md) ·
back to [my portfolio](../README.md) · previous: [Module 4](../Module04/README.md)

## Learning Goals

<a id="lg1"></a>
### LG1 — `fd`

Derive **functional dependencies** from a relation and identify candidate keys.

**Evidence:** [Round 1 — FDs tested with data](normalization-notes.md#round-1--see-it-functional-dependencies)

<a id="lg2"></a>
### LG2 — `normal-forms`

Normalize a relation to **1NF, 2NF, and 3NF**, explaining the anomaly each step removes.

**Evidence:** [Round 2 — anomalies](normalization-notes.md#round-2--break-it-the-three-anomalies), [Round 3 — 3NF](#round-3)

<a id="lg3"></a>
### LG3 — `denormalize`

**Denormalize deliberately** to speed up a hot read path, and predict what it costs on writes and storage.

**Evidence:** [Round 4](#round-4), [Round 5](#round-5)

<a id="lg4"></a>
### LG4 — `measure`

**Measure** the trade-off: query latency, write cost, and database size — before and after.

**Evidence:** [Benchmark table](#benchmark-table)

<a id="lg5"></a>
### LG5 — `decide`

Decide, and *defend*, where a schema should sit on the normalization spectrum for a given workload.

**Evidence:** [Round 6 — the memo](#round-6)

## Rounds 1–2

FDs (tested on 5 and 200,000 rows), the two ER sketches, the three anomalies, and the curiosities are in
**[normalization-notes.md](normalization-notes.md)**.

<a id="round-3"></a>
## Round 3 — Build it: 200k rows and 3NF

**Proves:** [LG2](#lg2)

[`setup.sql`](setup.sql) builds `flat_jobpart` (200,000 rows) in `normalize.db` (ignored by Git);
[`decompose.sql`](decompose.sql) splits it into `machine`, `part`, `job`, `job_part` — with `PRAGMA foreign_keys = ON` (output: [`decompose-results.txt`](decompose-results.txt)).

| flat_rows | job_part rows | machines | parts | jobs | rows lost by the split | rows invented |
|---:|---:|---:|---:|---:|---:|---:|
| 200,000 | 200,000 | 50 | 10 | 20,000 | **0** | **0** |

The decomposition still loads with foreign keys switched on (`PRAGMA foreign_key_check` finds nothing), and joining the four tables gives back exactly the flat rows (`EXCEPT` both ways is empty).

| normal form | what it removed here |
|---|---|
| 1NF | the flat table is already 1NF (one part per row, no lists) — unlike Module 2's `'P-1001,P-1002'` |
| 2NF | `part_no → part_price` depended on only *part* of the key `(job_id, part_no)` → moved to `part` |
| 3NF | `machine_id → site` was a non-key → non-key dependency → moved to `machine` |

<a id="round-4"></a>
## Round 4 — Race it

**Proves:** [LG3](#lg3), [LG4](#lg4)

[`race.py`](race.py) builds `report_jobpart`, warms the cache with one untimed run, then alternates A and B five times and takes the median (output: [`race-results.txt`](race-results.txt)).
Both queries return the **same 350 rows, total cost 722,610.0**.

**Plans:**

```text
A (normalized)                                        B (report_jobpart)
SCAN jp                                               SCAN report_jobpart USING INDEX ix_report_machine
SEARCH j USING INTEGER PRIMARY KEY (rowid=?)          USE TEMP B-TREE FOR GROUP BY
SEARCH m USING INDEX sqlite_autoindex_machine_1 (machine_id=?)
SEARCH p USING INDEX sqlite_autoindex_part_1 (part_no=?)
USE TEMP B-TREE FOR GROUP BY
```

| run | A — normalized | B — denormalized |
|---|---:|---:|
| B with `ix_report_machine` | **120.1 ms** | 148.6 ms |
| B without the index (`SCAN report_jobpart`) | 118.8 ms | **108.3 ms** |

**The "obvious" winner loses.** With its index, B is **24% slower** than the four-way join: the planner walks the whole index and then jumps into the table for every row.
Without the index, B wins — but only by about **9%**. The joins hit 50 machines, 10 parts and 20,000 jobs, all in cache, so the join is cheap and the scan dominates.

**Optional — make the join hurt** (`vendor` + `site_dim`, six-way join vs. one wide table; I used a separate table `report_wide` so `report_jobpart` stays intact). Same answer: **3,500 rows, 722,610.0**, as the workbook says.

| | A6 — six-way join | B6 — `report_wide` |
|---|---:|---:|
| median | 232.8 ms | **177.3 ms** (24% faster) |

With two more joins per row, the denormalized table pulls ahead — the win comes from removing **row-level join work**, not from "one table" as a slogan.

All timings: SQLite 3.53.1 (Python), Windows 10, warm cache. A first run of the same script gave higher numbers overall (A 169 / B 209 ms) but the **same order** — the ratios are the result, not the milliseconds.

<a id="round-5"></a>
## Round 5 — Price it

**Proves:** [LG3](#lg3), [LG4](#lg4)

[`price.sql`](price.sql) · output: [`price-results.txt`](price-results.txt)

Changing **one fact** — cnc-02 moves to Bielefeld:

| design | rows touched | time |
|---|---:|---:|
| 3NF (`machine`) | **1** | 4.4 ms |
| report table | **4,000** | 42.0 ms |

And the copy nobody updated (`report_wide`) now **disagrees**: it still says Gütersloh. That is the Round 2 update anomaly, with a price tag.

<a id="benchmark-table"></a>
### Benchmark table

| design | dashboard query (ms) | rows changed by one site update | storage (KB) | redundancy? |
|---|---:|---:|---:|---|
| Normalized (3NF) | 120.1 | 1 | 7,976 | none |
| Denormalized (report, with index) | 148.6 | 4,000 | 13,752 | site / technician / price on every row |
| Denormalized (report, no index) | 108.3 | 4,000 | 10,832 | same |
| *Stretcher: DuckDB, normalized* | *16.2* | — | — | none |
| *Stretcher: DuckDB, report table* | *9.7* | — | — | same |

Storage from `dbstat` (pages of the tables and their indexes): normalized 8,167,424 bytes; report table + index 14,082,048 bytes (table alone 11,091,968). The original flat table + its index: 14,880,768 bytes.

<a id="round-6"></a>
## Round 6 — Recommendation to the operations lead

> **To: Yasmin Kaya — Re: the machine-health dashboard**
>
> Keep the transactional tables (`machine`, `part`, `job`, `job_part`) in **3NF**: one site change touches 1 row there, but 4,000 rows in a copied table — and a copy that someone forgets is simply wrong, as our test showed.
> For the dashboard, a denormalized `report_jobpart` is **not worth it today**: on 200,000 rows it was 24% *slower* than the normalized join with its index, and only 9% faster without it, while using 1.7× the storage.
> It starts to pay when the join gets heavy — with two more dimensions it was 24% faster — so revisit it if the dashboard grows more lookups or the data stops fitting in memory.
> If we add it, it must be a **derived** table that nobody edits by hand: rebuild it on a schedule (for example every 5 minutes, inside one transaction), or keep it current with an `AFTER UPDATE` trigger on `machine` and `part` like the ones from Module 4.
> Never write to it directly, and never drop the normalized tables it is built from.
> Worth knowing: a columnar engine (DuckDB) ran the *normalized* query in 16 ms, 7× faster than SQLite's best — for analytics, a different engine may beat any copy we make.

<a id="round-7"></a>
## Round 7 — Stretcher: DuckDB

[`duckdb_compare.py`](duckdb_compare.py) copies the five tables into an in-memory DuckDB 2.0.0 (output: [`duckdb-results.txt`](duckdb-results.txt)). Same 350 rows, same total.

| engine | A — normalized | B — report table |
|---|---:|---:|
| SQLite (best case) | 118.8 ms | 108.3 ms |
| DuckDB | **16.2 ms** | **9.7 ms** |

DuckDB is about **7× faster** on the normalized query than SQLite is on the denormalized one. A columnar, vectorized engine reads only the columns it needs and joins in batches — so for this workload it removes most of the reason for the report table. The table still halves DuckDB's time, but 16 ms is already fast enough for a dashboard that refreshes every 30 seconds.

## Reflection 5

[Reflection 5](../Reflections/ref05.md)
