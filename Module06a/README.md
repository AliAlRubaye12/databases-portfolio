# Module 6a — The Analytical Engine (DuckDB)

Course workbook: [Module 6a](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/06a-duckdb-analytical-engine.md) ·
back to [my portfolio](../README.md) · previous: [Module 5](../Module05/README.md)

## Learning Goals

<a id="lg1"></a>
### LG1 — `parquet`

Move a table out of SQLite into **Parquet** reproducibly, from a script.

**Evidence:** [Tasks 1–2](#task-1-2)

<a id="lg2"></a>
### LG2 — `race`

Run the **same aggregate** in SQLite and DuckDB and report the difference honestly (interleaved runs, median).

**Evidence:** [Task 3](#task-3)

<a id="lg3"></a>
### LG3 — `explain-analyze`

Read **`EXPLAIN ANALYZE`** and name the operator and row count that dominate.

**Evidence:** [Task 4](#task-4)

<a id="lg4"></a>
### LG4 — `boundary`

State, with a number, **where DuckDB is the wrong engine**.

**Evidence:** [Task 5](#task-5)

<a id="lg5"></a>
### LG5 — `refresh`

Recommend **what moves to the analytical copy** and how that copy stays fresh.

**Evidence:** [Task 6 — memo](#task-6), [refresh.py](duckdb-notes.md#refreshpy--two---check-runs-intense-track)

Notes, discussion answers, curiosities and stretchers: **[duckdb-notes.md](duckdb-notes.md)**.

<a id="task-1-2"></a>
## Tasks 1–2 — Build the history and convert to Parquet

**Proves:** [LG1](#lg1)

[`prepare.py`](prepare.py) stretches Module 5's `report_jobpart` to ten quarters; [`to_parquet.py`](to_parquet.py) lets DuckDB do the same expansion straight into Parquet and then compares both sides (outputs: [`prepare-results.txt`](prepare-results.txt), [`to-parquet-results.txt`](to-parquet-results.txt)).

| | SQLite `history.db` | `report_history.parquet` |
|---|---:|---:|
| rows | 2,000,000 | 2,000,000 |
| `SUM(part_price)` | 21,000,000.0 | 21,000,000.0 |
| dates | 2026-01-01 … 2028-06-27 | 2026-01-01 … 2028-06-27 |
| file size | **112.6 MB** | **2.40 MB** (≈47× smaller) |

The CSV is written with `encoding="utf-8"`, so "Gütersloh" survives on Windows. The database, CSV and Parquet files are ignored by Git — the scripts rebuild them.

<a id="task-3"></a>
## Task 3 — The race

**Proves:** [LG2](#lg2)

[`race.py`](race.py): one untimed warm-up per engine, then 5 interleaved runs, median and [min–max]. I added a check that both engines return **the same answer** ([output](race-results.txt)).

| query | SQLite | DuckDB | ratio | same answer? |
|---|---:|---:|---:|---|
| dashboard | 3,177.7 ms [3,103–3,426] | 21.3 ms [20.7–29.0] | **149×** | ✅ 350 rows |
| monthly — workbook SQL | 2,601.1 ms | 59.4 ms | 44× | ❌ **50 vs 1,500 rows** |
| monthly — SQLite spelling fixed | 3,830.6 ms | 62.7 ms | **61×** | ✅ 1,500 rows |
| one day, no index | 274.8 ms | 8.3 ms | 33× | ✅ |
| one day, **with index** | **6.4 ms** | 8.9 ms | **0.7× — SQLite wins** | ✅ |

**The workbook's monthly query gives a wrong answer in SQLite.** `strftime(done_on, '%Y-%m')` is DuckDB's argument order. SQLite reads it as `strftime(format, date)`, gets `NULL` for every row, and puts all two and a half years into one "month". It even looked faster. Without the answer check, this bug would have been reported as a speed result.

The monthly ratio (61×) is lower than the dashboard's (149×): `strftime` runs once per row, and that per-row work is a bigger share of DuckDB's short time than of SQLite's long scan.

<a id="task-4"></a>
## Task 4 — The plan

**Proves:** [LG3](#lg3)

[`plan.py`](plan.py) ([output](plan-results.txt)), DuckDB `EXPLAIN ANALYZE` for the dashboard, read bottom-up:

```text
Table Scan     READ_PARQUET   Projections: machine_id, site, technician, part_price
               Row Groups Scanned: 17 / 17          2,000,000 rows    <- dominates
Projection     2,000,000 rows
Hash Group By  Groups: #0, #1, #2   Aggregates: sum(#3)   350 rows
Summary        Total Time 0.0300 s   Data Read: 185.6 kB
```

- **The scan dominates:** 2,000,000 rows come in, 350 groups go out.
- **Four columns, not seven:** the data read is **185.6 kB**. The same scan as `SELECT *` reads **2.1 MB** — the row count stays, the projections and bytes change.
- SQLite's plan for the same question is one `SCAN report_history` over full rows plus `USE TEMP B-TREE FOR GROUP BY` — a *prediction*, where DuckDB's `EXPLAIN ANALYZE` is a *measurement*.

<a id="task-5"></a>
## Task 5 — The boundary

**Proves:** [LG4](#lg4)

[`boundary.py`](boundary.py), 1,000 single-row statements, median of 5 ([output](boundary-results.txt)):

| | SQLite | DuckDB | DuckDB slower by |
|---|---:|---:|---:|
| inserts, one by one | 2.2 ms | 1,037.9 ms | ≈480× |
| inserts, `executemany` | 1.0 ms | 521.5 ms | ≈500× |
| lookups by id | 2.7 ms | 709.7 ms | ≈265× |

**For Kortmann, DuckDB is the wrong engine for anything that writes or reads one row at a time** — recording a job, a sensor reading, a lookup by id. 1,000 inserts take about a second in DuckDB and 2 ms in SQLite. Batching halves DuckDB's time but leaves the gap at ≈500×.

<a id="task-6"></a>
## Task 6 — Memo to Lea Winter and Yasmin Kaya

> **Re: moving the month-end report**
>
> Move the **history for reporting** — the job–part rows with site, technician and price — to a Parquet file that DuckDB reads. Keep everything the line *writes* in SQLite: jobs, parts, machines, and every single-row lookup.
> On 2 million rows (two and a half years), the dashboard query took **3.2 s in SQLite and 21 ms in DuckDB** (149×), and the monthly report **3.8 s vs 63 ms** (61×) — while the file is **2.4 MB instead of 113 MB**, and the report no longer blocks the writer at all.
> Do **not** move recording jobs or looking up one job: 1,000 single inserts took 2 ms in SQLite and about 1 s in DuckDB.
>
> **How the copy stays fresh:** `refresh.py` rebuilds the Parquet from SQLite in about 8 seconds — run it every night after the last shift (a scheduled task), and once by hand before the month-end report. It writes to a temporary file and swaps it in only when complete, so the report never reads a half-written file.
> `refresh.py --check-only` compares row count and total price between SQLite and the copy and exits with an error on a mismatch; the scheduled task should alert the shift lead when it fails.
> **What a stale copy breaks:** the report silently misses the newest jobs — in my test a single price change of 1 was caught by the check. **What the check does *not* protect against:** two changes that cancel out (one price +1, another −1) keep count and sum equal, and the check said OK. If exact figures matter, add per-month sums to the check, or simply rebuild before every report — at 8 seconds that is cheap.
>
> **Compression:** zstd makes the file 41% smaller (1.41 MB) at the same speed; worth switching once the history no longer fits in memory.

<a id="task-7"></a>
## Task 7 — Homework and stretchers

- **Core:** zstd copy 2.40 MB → 1.41 MB, same dashboard time (20.6 vs 19.2 ms); refresh paragraph in the memo above.
- **Intense track:** [`refresh.py`](refresh.py) with `--check` and `--check-only`; two idempotent runs, a caught stale copy, and the blind spot — [`refresh-results.txt`](refresh-results.txt).
- **S2:** sorting by date lets DuckDB skip row groups: **17 / 17 → 2 / 17** scanned for one month ([`stretch.py`](stretch.py)).

## Reflection 6a

[Reflection 6a](../Reflections/ref06a.md)
