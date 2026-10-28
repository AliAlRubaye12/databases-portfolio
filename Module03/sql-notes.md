# Module 3 — SQL notes (pod study + curiosities)

Back to [Module 3](README.md).

## References I used

| Source | The one concept I understood best from it |
|---|---|
| [Course workbook, Module 3](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/03-llm-assisted-sql-and-query-profiling.md) | The plan is evidence, the clock is a symptom — a plan change with no time change is still a real result. |
| [SQLite: EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html) | Read the plan as a loop nest: the top line is the outer loop. |

## Task A — Plan safari

On `Module02/legacy.db`. Script: [`safari.sql`](safari.sql) · output: [`safari-results.txt`](safari-results.txt).
The index is dropped at the end, so Module 2 stays reproducible.

| query | predicted | before index | after `ix_job_tech` |
|---|---|---|---|
| `technician = 'Beier'` | SCAN → SEARCH | `SCAN maint_job` | `SEARCH maint_job USING INDEX ix_job_tech (technician=?)` |
| `machine_name = 'cnc-02'` | SCAN, stays SCAN | `SCAN machine` | `SCAN machine` — the index is on a different table |
| `technician LIKE '%ei%'` | SCAN, stays SCAN | `SCAN maint_job` | `SCAN maint_job` — a leading `%` means no starting point in the sorted index |

**Breaking the index on purpose:**

| `WHERE` | plan with the index | why |
|---|---|---|
| `lower(technician) = 'beier'` | `SCAN` | the index stores `technician`, not `lower(technician)` |
| `technician LIKE 'Bei%'` | `SCAN` — **surprising** | `LIKE` ignores upper/lower case, the index is case-sensitive, so it cannot be used |
| `technician GLOB 'Bei*'` | `SEARCH … (technician>? AND technician<?)` | `GLOB` is case-sensitive, so the prefix becomes a range on the index |
| `SELECT technician … = 'Beier'` | `SEARCH … USING COVERING INDEX` | only the indexed column is needed, the table is never opened |

## Task B — Algebra check

Query: the single-day lookup from Task 2.

```sql
SELECT o.order_id, o.ordered_on, c.name
FROM orders o JOIN customer c ON c.customer_id = o.customer_id
WHERE o.ordered_on = '2026-02-14';
```

```text
π order_id, ordered_on, name ( σ ordered_on = '2026-02-14' (orders) ⋈ customer_id customer )
```

Written with Claude, then checked against the SQL and the plan:
- **σ pushed down onto `orders`** — the same thing the planner does: `SEARCH o USING INDEX ix_orders_ordered_on (ordered_on=?)` runs first, then customer is looked up per order.
- **A real difference between the two:** relational algebra works with *sets* (no duplicate rows), SQL works with *bags* (duplicates stay unless you write `DISTINCT`). For this query it does not matter, because `order_id` is unique.

## LLM Q&A (verified by running it)

Model: Claude (Opus 5.5).

| question | answer (short) | how I verified it |
|---|---|---|
| When does SQLite use a *covering* index? | When the index holds every column the query needs, so the table is never opened. | `SELECT technician … WHERE technician = 'Beier'` → `USING COVERING INDEX`; `SELECT *` → plain `USING INDEX`. |
| Why can't an index help `LIKE '%ei%'`? What could? | An index is sorted from the first letter; a leading `%` gives no starting point. Full-text search (FTS5) or a trigram index could. | `SCAN maint_job` before and after the index. |
| Is a `SELECT` alias in `WHERE` an error? | In standard SQL yes, because `WHERE` runs before `SELECT`. | **Partly wrong for SQLite** — see [clause order](#clause-order). |
| Will an index always make a query faster? | No — for a query that reads most of a table, a full scan can win. | `ix_orderline_order` made the dashboard **9× slower** ([Task 2](README.md#task-2)). |

<a id="clause-order"></a>
## Clause order — a claim that did not hold in SQLite

Written `SELECT … FROM … WHERE … GROUP BY … HAVING … ORDER BY`, evaluated `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY`.
Script: [`clause-order.sql`](clause-order.sql) · output: [`clause-order-results.txt`](clause-order-results.txt).

| query | result |
|---|---|
| `SELECT qty * 2 AS double_qty … WHERE double_qty > 7` | **works in SQLite** — a non-standard extension. The same query fails in PostgreSQL. |
| `SELECT SUM(qty) AS total … WHERE total > 10 GROUP BY …` | fails: `misuse of aggregate: SUM()` — `WHERE` runs before the groups exist |
| `… GROUP BY order_id HAVING total > 10` | works — `HAVING` runs after `GROUP BY` |

So "it runs in SQLite" does not mean "it is portable SQL" — worth knowing when an LLM-written query moves to a server later.

## Curiosities (the harvest)

| curiosity | source |
|---|---|
| Revenue per city ranges from 2.8 M to 11.2 M, but every city has exactly 500 customers and the same average price (~68–70). The cause: city and quantity are both decided by the order number modulo 4, so **every** Bielefeld line has `qty = 4` and every Paderborn line `qty = 1`. My first guess ("expensive products") was wrong — a query proved it. Generated data can hide patterns like this. | [setup.sql](setup.sql), `x % 4` in two places |
| `BLOOM FILTER ON o` appeared in the dashboard plan after adding the date index — a plan line the workbook never mentions. | [bench-results.txt](bench-results.txt) |
| `WITH RECURSIVE` makes 240,000 rows out of nothing: one row, then "plus one" until the limit. | [setup.sql](setup.sql) |
| `LIKE 'Bei%'` cannot use a normal index, but `GLOB 'Bei*'` can. | [safari-results.txt](safari-results.txt) |
| The `sqlite3` shell (3.53.4) and Python's built-in `sqlite3` (3.53.1) are different versions on the same laptop — plans could differ between them. | `sqlite3 --version`, [uv-check](../Module01/README.md#task-3) |

## Task C — with a neighbouring pod

<!-- Compare plans for the same query (check `sqlite3 --version` first), name the plan that surprised each pod most,
     and swap curiosities. Anything nobody could place goes to #sql-questions. -->

- _(to add after the pod pairing)_
