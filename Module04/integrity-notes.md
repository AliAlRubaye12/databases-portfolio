# Module 4 — Integrity notes (pod study)

Back to [Module 4](README.md).

## References I used

| Source | The one concept I understood best from it |
|---|---|
| [Course workbook, Module 4](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/04-integrity-constraints-and-triggers.md) | Integrity has three layers — entity, referential, domain — and each maps to a SQL feature. |
| [SQLite: STRICT tables](https://www.sqlite.org/stricttables.html) | `STRICT` forces each column to hold its declared type. |
| [SQLite: Foreign Key Support](https://sqlite.org/foreignkeys.html) | Foreign keys must be switched on for every new connection. |

## Task A — The acceptance test

Script: [`acceptance.sql`](acceptance.sql) · output: [`acceptance-results.txt`](acceptance-results.txt)

**Without constraints, all 9 junk rows landed** — including an empty row, `'abc'` as a sensor id, an exact duplicate, `1e308`, and −273.16 °C (below absolute zero).

**With constraints** (`STRICT`, `NOT NULL`, `CHECK`, `PRIMARY KEY`), one insert at a time:

| insert | rejected by | layer | exact error |
|---|---|---|---|
| `(1,'temp_c',9000)` | `CHECK` | domain | `CHECK constraint failed: value BETWEEN -273.15 AND 5000` |
| `(1,'temp_c','hot')` | `STRICT` | domain (type) | `cannot store TEXT value in REAL column c.value` |
| `(2,'bogus',-500)` | `CHECK` | domain | `CHECK constraint failed: metric IN ('temp_c','vib_rms','spindle_load')` |
| `(NULL,NULL,NULL)` | `NOT NULL` | entity | `NOT NULL constraint failed: c.sensor_id` |
| `('abc','temp_c',20)` | `STRICT` | domain (type) | `cannot store TEXT value in INTEGER column c.sensor_id` |
| `(1,'temp_c',41.5)` twice | `PRIMARY KEY` | entity | `UNIQUE constraint failed: c.sensor_id, c.metric, c.value` |
| `(1,'TEMP_C',1e308)` | `CHECK` | domain | `CHECK constraint failed: metric IN (...)` — capital letters count as a different value |
| `(1.5,'',-273.16)` | `STRICT` | domain (type) | `cannot store REAL value in INTEGER column c.sensor_id` — the type is checked before the `CHECK`s |

**Surprises:**
- **`STRICT` accepted the text `'20'`** in a `REAL` column — it looks like a number, so SQLite converts it to `20.0`. Only real text like `'hot'` is refused.
- **`CHECK` lets `NULL` through.** A check that comes out "unknown" counts as passed. Only `NOT NULL` stops a missing value.
- **Plausible but wrong still gets in:** a vibration of `4000` passes, because the range −273.15…5000 is written for temperatures. A good schema needs a range *per metric* (or a check that depends on the metric).

## LLM Q&A (verified by running it)

Model: an AI assistant (LLM).

| question | answer (short) | how I verified it |
|---|---|---|
| Which layer can a `CHECK` never cover? | Referential — a `CHECK` only sees its own row and cannot look into another table. | The orphan sensor 99 was stopped by the `FOREIGN KEY`, not by any `CHECK` ([Task 1](README.md#task-1)). |
| A rule a `CHECK` cannot express but a trigger can? | "Readings must arrive in time order" — it needs the *previous* rows. | A `BEFORE INSERT` trigger with `RAISE(ABORT)` rejected a late reading ([Task 5](README.md#task-5)). |
| `BEFORE` vs `AFTER` — which one can reject a row? | Often answered "only `BEFORE`". **Not true in SQLite:** both can, with `RAISE(ABORT)`. | An `AFTER INSERT` trigger with `RAISE(ABORT)` rolled the insert back — 1 row kept out of 2. |
| Why is `PRAGMA foreign_keys` per connection? What breaks if a tool forgets it? | Backwards compatibility; a tool that forgets it writes orphans without any error. | A new `sqlite3` connection showed `foreign_keys = 0` and accepted the orphan reading for sensor 99 ([`fk-off-results.txt`](fk-off-results.txt), rolled back). |

## Task B — With another pod

<!-- The most surprising thing an unconstrained table accepted, the hardest constraint to get right,
     agreed points, and anything for #sql-questions. -->

Our proposed points for the discussion:
1. `CHECK` is not `NOT NULL` — a `NULL` passes every `CHECK`.
2. `STRICT` is not "no conversion" — `'20'` still becomes `20.0`.
3. Every tool that writes needs `PRAGMA foreign_keys = ON`, or the foreign key is only decoration.

From the other pod: _(add here)_
