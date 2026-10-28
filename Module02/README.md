# Module 2 — Data Contracts & Reading Legacy Schemas (ERD Audits)

Course workbook: [Module 2](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/02-data-contracts-and-legacy-schemas.md) ·
back to [my portfolio](../README.md) · previous: [Module 1](../Module01/README.md)

## Learning Goals

<a id="lg1"></a>
### LG1 — `er-model`

Reconstruct an **ER/EER model** (entities, attributes, keys, relationships, cardinalities) from an undocumented SQL schema.

**Evidence:** [Task 1 — ER audit](#task-1)

<a id="lg2"></a>
### LG2 — `defects`

Identify **integrity defects** — missing foreign keys, orphan rows, redundant data, normalization violations — with queries, not intuition.

**Evidence:** [Task 2 — defects](#task-2)

<a id="lg3"></a>
### LG3 — `keys`

Distinguish an **entity relationship** from an attribute, and a **surrogate key** from a natural key, and justify the choice.

**Evidence:** [ER audit — entities and keys](er-audit.md#1-entities-attributes-intended-keys), [Pod study](#task-a)

<a id="lg4"></a>
### LG4 — `contract`

Express a schema as a **code-first data contract** (Pydantic / SQLAlchemy) that an application can enforce.

**Evidence:** [Task 3 — contract](#task-3)

<a id="lg5"></a>
### LG5 — `requirements`

Write the **requirements the schema forgot**: the business rules nobody encoded.

**Evidence:** [Forgotten requirements](#requirements)

<a id="task-a"></a>
## Pod study (Tasks A–C)

**Proves:** [LG1](#lg1), [LG3](#lg3)

See [study-log.md](study-log.md): the four Task B sketches with a `CREATE TABLE` + `COUNT` proof,
LLM answers each verified against `legacy.db`, and remarkable findings.
_(Still to add: the other pod's feedback on our proposed points, after the pod pairing.)_

<a id="task-1"></a>
## Task 1 — Reconstruct the ER model

**Proves:** [LG1](#lg1), [LG3](#lg3)

Full audit with the Mermaid ER diagram and the count proofs: **[er-audit.md](er-audit.md)**.

Short version: the designer meant five entities — Machine, Part, MaintenanceJob, Technician, and a JobPart junction —
but declared only three tables, no keys, and no relationships. Both 1:n relationships live in matching text values,
and the m:n between jobs and parts is packed into a comma-separated string.

<a id="task-2"></a>
## Task 2 — Integrity defects, proven with queries

**Proves:** [LG2](#lg2)

Queries: [`defects.sql`](defects.sql) · full output: [`defects-results.txt`](defects-results.txt)

| # | Defect | Proof (query result) | What breaks in production |
|---|---|---|---|
| 1 | Orphan job | job 3 → `cnc-05`, which is not in `machine` | The job cannot be tied to a site or serial, so its cost and downtime vanish from every machine report. |
| 2 | Duplicate natural key | `P-1003` appears **2** times | Any join on `part_no` doubles that part — stock counts and job costs come out too high. |
| 3 | Price stored as text | `unit_price < '15'` returns only P-1001; numerically it should also return P-1003 (9.90) | `'9.90' < '15'` is false in text order (`'9'` > `'1'`), so price filters and invoices are silently wrong. |
| 4 | Date stored as free text | `RANDOM-NAME` has `installed = 'unknown'` | Age and warranty calculations crash or skip the machine without anyone noticing. |
| 5 | m:n list as a "key" | the join returns jobs 2 and 3 only; job 1 (`P-1001,P-1002`) silently disappears | Exactly Anke's question — *which parts did we replace?* — under-reports every multi-part job, and still looks like success. |

**Two defects combine.** In Defect 5's join, job 2 appears **twice** ("Coolant filter" ×2): the duplicate part row
from Defect 2 doubles every join on `P-1003`. One bad row corrupts the result of a query that has nothing to do with duplicates.

<a id="task-3"></a>
## Task 3 — The data contract in code

**Proves:** [LG4](#lg4)

- [`contract.py`](contract.py) — the workbook contract: Pydantic models for the application, SQLAlchemy tables for the database.
- [`contract-ddl.sql`](contract-ddl.sql) — the corrected DDL it emits (`uv run python Module02/contract.py`).
- [`check_legacy.py`](check_legacy.py) — my verification: it pushes every legacy row through the contract. Output: [`check-legacy-results.txt`](check-legacy-results.txt).

| Legacy row | Rejected by | Message |
|---|---|---|
| `RANDOM-NAME`, installed `unknown` | Pydantic (`installed: date`) | Input should be a valid date |
| job 3 → `cnc-05` | no `machine_id` to map to | orphan |
| second `P-1003` | database (`part_no` PRIMARY KEY) | UNIQUE constraint failed |
| `job_part` row for job 99 | database (foreign key) | FOREIGN KEY constraint failed |

**Model vs. database — where each rule lives:**

- **In the database:** keys, uniqueness, foreign keys, `NOT NULL`, numeric and date types. These must hold no matter which program
  writes the data — a script, a CLI, or a future app — so they belong to the data itself.
- **In the model (Pydantic):** rules that are business conventions and may change, like *serial numbers start with `SN-`*,
  and nicer error messages at the edge of the application, before anything reaches the database.
- **Caveat found while verifying:** SQLite **ignores foreign keys unless `PRAGMA foreign_keys = ON`** is set on each connection.
  Without it, the dangling `job_part` row above would have been accepted.

**What the contract still gets wrong (verify, don't trust):**

- The corrected `machine` table has **no `machine_name`** column. Migrating to it loses `cnc-01` — the name everyone in the shop uses.
  It should keep `machine_name` as `NOT NULL UNIQUE`.
- `technician` is still free text in `maint_job`. My ER model has a Technician entity; the contract does not.

<a id="requirements"></a>
## Requirements the schema forgot

**Proves:** [LG5](#lg5)

1. Every maintenance job belongs to exactly one existing machine.
2. A part number identifies exactly one part; prices are money (two decimals, ≥ 0).
3. A job lists each part at most once (the `job_part` primary key) — or, if the same part can be used twice, a `quantity` column is missing.
4. `done_on` cannot be before the machine's `installed` date, and not in the future.
5. Every machine has a known install date; "unknown" is not allowed.
6. A technician is a known person, not any string.

## Reflection 2

[Reflection 2](../Reflections/ref02.md)
