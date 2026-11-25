# Module 6a — DuckDB notes

Back to [Module 6a](README.md).

## Module 5 recap — my numbers vs. the workbook's

| | workbook recap | mine ([Module 5](../Module05/README.md#benchmark-table)) |
|---|---|---|
| storage, normalized | ≈ 4.1 MB | 8.2 MB — I counted the tables **and** their primary-key indexes (`job_part`'s two-column key is a big index) |
| storage, denormalized | ≈ 11.1 MB | 11.1 MB (table only) — same |
| rows touched by one site update | 1 vs 4,000 | 1 vs 4,000 — same |
| dropping the report index | faster | faster (149 → 108 ms) — same |

## Discussion answers (with tests)

**Task 1 — why exactly 10 × 200,000?** The `WITH RECURSIVE` gives k = 0…9, and the comma join pairs every one of the 200,000 rows with every k. Ten copies, each shifted by `k × 91` days. The dates run 2026-01-01 … 2028-06-27 — about two and a half years, as planned.

**Task 2 — same data or just same size?** A row count alone would not convince me (2,000,000 rows of anything). I checked **four** things on both sides: row count, `SUM(part_price)`, first date and last date — all identical ([`to-parquet-results.txt`](to-parquet-results.txt)). Even that is not proof (see the blind spot below), but it would catch a missing quarter or a wrong shift.

**Task 3 — what would make SQLite win?** A point query on an index. With `ix_history_done_on`, one day took **6.4 ms in SQLite vs 8.9 ms in DuckDB**. Without the index SQLite needed 275 ms.

**Task 4 — which operator dominates?** The scan: `Table Scan … 2,000,000 rows`, reading only 4 of 7 columns (**185.6 kB** of data read vs **2.1 MB** for `SELECT *`). Grouping only produces 350 rows.
Note: DuckDB's per-operator times are summed over its worker threads, so `Hash Group By 90 ms` can be larger than the total of 30 ms wall-clock.

**Task 5 — where is DuckDB the wrong tool?** Request-per-row work: 1,000 single inserts took **2.2 ms in SQLite vs 1,038 ms in DuckDB** (≈480×); 1,000 lookups by id **2.7 ms vs 710 ms**. `executemany` halves DuckDB's insert time but the gap stays ≈500×, because every statement still goes through DuckDB's planning and its batch-oriented machinery. The *application* would have to change: collect rows and load them in bulk (`COPY`, or append a whole file).

## Things the workbook did not tell me

| curiosity | evidence |
|---|---|
| **The workbook's monthly query is wrong in SQLite.** `strftime(done_on, '%Y-%m')` is DuckDB's argument order; SQLite expects `strftime('%Y-%m', done_on)`. In SQLite the workbook version returns `NULL` for every row: **0 distinct months instead of 30**, so the "monthly" report has 50 rows instead of 1,500 — and it ran *faster* because it did less work. | [`race-results.txt`](race-results.txt) |
| **An index that helps one query can hurt another.** After adding `ix_history_done_on` for the one-day lookup, SQLite used it for the dashboard too — where every row matches — and the dashboard went from **3.2 s to 7.4 s**. `ANALYZE` did not change the planner's mind. | [`index-trap-results.txt`](index-trap-results.txt) |
| `date_trunc('month', …)` did not improve DuckDB's monthly ratio here (83 ms vs 63 ms) — but I wrapped it in `strftime` to get the same text output, so it does two steps instead of one. Not a fair test of the workbook's claim. | [`race-results.txt`](race-results.txt) |
| My SQLite is about **5× slower** than the workbook's machine (dashboard 3.2 s vs ≈600 ms), DuckDB about 3× (21 ms vs ≈6 ms) — so my ratios are *bigger* (149× vs ≈100×). The ratio travels, but it also depends on the laptop. | [`race-results.txt`](race-results.txt) |

## Stretchers

**S2 — row-group statistics** ([`stretch-results.txt`](stretch-results.txt)): in the original file every one of the 17 row groups spans the whole date range, so a one-month query scans **17 / 17**. Written sorted by `done_on`, each group covers about two months and the same query scans **2 / 17** — 5.6 ms → 3.2 ms. Small at 2M rows; at 200M it decides the query.

**S3 — compression:** snappy **2.40 MB** → zstd **1.41 MB** (41% smaller), dashboard 20.6 ms vs 19.2 ms — same speed.

## refresh.py — two `--check` runs (intense track)

```text
== refresh.py --check, run 1
rows 2,000,000  checksum SUM(part_price) 21000000.0  parquet 2.46 MB  elapsed 7,588 ms
check: OK
== refresh.py --check, run 2 (idempotent?)
rows 2,000,000  checksum SUM(part_price) 21000000.0  parquet 2.46 MB  elapsed 7,704 ms
check: OK
```

Same rows, same checksum, same size twice — idempotent. (The bytes may still differ between runs; the numbers are what must match. This rebuild writes 2.46 MB instead of the 2.40 MB from `to_parquet.py`, because it is written from a different source and with explicit column types.)

Full run, including the failure cases: [`refresh-results.txt`](refresh-results.txt).

## Exchanges with the nearest pod

- _(to add after class)_
