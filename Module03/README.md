# Module 3 — LLM-Assisted SQL & Query Profiling

Course workbook: [Module 3](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/03-llm-assisted-sql-and-query-profiling.md) ·
back to [my portfolio](../README.md) · previous: [Module 2](../Module02/README.md)

## Learning Goals

<a id="lg1"></a>
### LG1 — `dql`

Build complex **DQL** queries: joins, aggregation with `GROUP BY`/`HAVING`, subqueries, and window functions.

**Evidence:** [Task 1 — dashboard query](#task-1), [clause order tests](sql-notes.md#clause-order)

<a id="lg2"></a>
### LG2 — `plans`

Read **`EXPLAIN QUERY PLAN`** as *primary evidence*: say what the engine will do for a given query, tell a `SCAN` from a `SEARCH`, and a table lookup from a covering index.

**Evidence:** [Task A — plan safari](sql-notes.md#task-a--plan-safari), [Task 1 — predicted vs. real plan](#task-1)

<a id="lg3"></a>
### LG3 — `index`

**Benchmark** the effect of an index and explain when the planner ignores one.

**Evidence:** [Task 2 — index benchmark](#task-2)

<a id="lg4"></a>
### LG4 — `verify-llm`

Generate a query with an **LLM**, then **verify** it: correctness, performance, and edge cases.

**Evidence:** [Task 1](#task-1), [Task 2](#task-2)

<a id="lg5"></a>
### LG5 — `injection`

**Prevent SQL injection** with bound parameters and demonstrate why string concatenation is exploitable.

**Evidence:** [Task 3 — injection drill](#task-3)

## Pod study (Tasks A–C)

**Proves:** [LG2](#lg2)

See [sql-notes.md](sql-notes.md): the plan safari with predictions next to the real plans, the algebra check,
verified LLM answers, and the curiosities collection. _(Task C — comparing plans with another pod — still to do.)_

## Setup

[`setup.sql`](setup.sql) builds `warehouse.db` (ignored by Git, rebuild any time):

```bash
sqlite3 Module03/warehouse.db ".read Module03/setup.sql"
```

Result: 2,000 customers, 500 products, **60,000** orders, **240,000** order lines, 5.4 MB.

Two of the scaffolding questions, answered by running them:

- `x = 540` gives `'+0 days'`, so the date **wraps back to `2025-01-01`** — the dates repeat every 540 orders.
- Without `printf('%05d', x)`, `'SKU-9' < 'SKU-10'` is **false** (text compares character by character). With padding, `'SKU-00009' < 'SKU-00010'` is true.

<a id="task-1"></a>
## Task 1 — Ask the LLM, then check the plan

**Proves:** [LG1](#lg1), [LG2](#lg2), [LG4](#lg4)

**Model:** Claude (Opus 5.5). **Prompt** (from the workbook):

> SQLite schema: `customer(customer_id, name, city)`, `product(product_id, sku, price)`, `orders(order_id, customer_id, ordered_on, status)`, `order_line(order_id, product_id, qty)`. Write a query that returns, for each city, the number of distinct customers and the total revenue (sum of `qty*price`) of orders placed in 2025, ordered by revenue descending.

**The LLM's SQL:**

```sql
SELECT c.city,
       COUNT(DISTINCT c.customer_id) AS customers,
       SUM(ol.qty * p.price)         AS revenue
FROM customer c
JOIN orders o      ON o.customer_id = c.customer_id
JOIN order_line ol ON ol.order_id   = o.order_id
JOIN product p     ON p.product_id  = ol.product_id
WHERE strftime('%Y', o.ordered_on) = '2025'
GROUP BY c.city
ORDER BY revenue DESC;
```

**Predicted plan** (written before running): `SCAN order_line`, then `SEARCH` orders, customer and product by their primary keys, then temp B-trees for `GROUP BY` and `ORDER BY`.

**Actual plan** ([`task1.sql`](task1.sql), output in [`task1-results.txt`](task1-results.txt)):

```text
|--SCAN ol
|--SEARCH o USING INTEGER PRIMARY KEY (rowid=?)
|--SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
|--SEARCH p USING INTEGER PRIMARY KEY (rowid=?)
|--USE TEMP B-TREE FOR GROUP BY
|--USE TEMP B-TREE FOR count(DISTINCT)
`--USE TEMP B-TREE FOR ORDER BY
```

My prediction was right except for one line I did not expect: **`USE TEMP B-TREE FOR count(DISTINCT)`** — counting distinct values needs its own sorted structure.

| city | customers | revenue |
|---|---:|---:|
| Bielefeld | 500 | 11,242,176 |
| Gütersloh | 500 | 8,422,344 |
| Münster | 500 | 5,493,504 |
| Paderborn | 500 | 2,815,656 |

**Correctness:**
- The result is **identical** to the workbook reference query (an `EXCEPT` in both directions returns no rows), and the plans are the same.
- `DISTINCT` is essential: without it Bielefeld would report **40,908** "customers" instead of 500, because every order line repeats the customer.
- No customer is lost by the inner join (0 customers without 2025 orders) — but on real data, a city with no 2025 orders would silently disappear from the report.
- `strftime('%Y', ordered_on) = '2025'` is correct but wraps the column in a function, so it can **never** use an index on `ordered_on`. The reference's range (`>= '2025-01-01' AND < '2026-01-01'`) can. Today the plan does not change, because `order_line` is scanned anyway — but it is the wrong habit.

<a id="task-2"></a>
## Task 2 — Index benchmark: prove it or disprove it

**Proves:** [LG3](#lg3), [LG4](#lg4)

**The LLM's optimization advice:** add `ix_orders_ordered_on`, `ix_orderline_order`, and `ix_orderline_product`. I tested each one separately with [`bench.py`](bench.py) (median of 5 runs; fast queries amortized over a batch; `ANALYZE` after each index). Full output with every plan: [`bench-results.txt`](bench-results.txt).

| query (ms) | no index | + ix_orders_ordered_on | + ix_orderline_order | + ix_orderline_product |
|---|---:|---:|---:|---:|
| dashboard | 181.7 | 185.4 | **1657.9** | 1653.6 |
| single day | 4.279 | **0.241** | 0.302 | 0.235 |
| single day, `date()` | 9.041 | 8.889 | 9.046 | 8.945 |
| one product | 15.04 | 14.32 | 14.74 | **2.54** |

SQLite 3.53.1 (Python's built-in module), Windows 10.

**Plan vs. time, step by step:**

| step | plan changed? | time changed? |
|---|---|---|
| `+ ix_orders_ordered_on`, dashboard | **yes, slightly** — a `BLOOM FILTER ON o` appears; `order_line` is still scanned | no (181.7 → 185.4, noise) |
| `+ ix_orders_ordered_on`, single day | **yes** — `SCAN o` → `SEARCH o USING INDEX ix_orders_ordered_on (ordered_on=?)` | **18× faster** |
| `+ ix_orderline_order`, dashboard | **yes** — now starts from the date index and looks up `order_line` per order | **9× slower** |
| `+ ix_orderline_product`, dashboard | no | no |
| `+ ix_orderline_product`, one product | **yes** — `SCAN order_line` → `SEARCH … USING INDEX ix_orderline_product` | **6× faster** |

**Negative results:**

- **`ix_orderline_order` makes the dashboard 9× slower.** The dashboard needs **162,300** of the 240,000 order lines (40,575 of the 60,000 orders are from 2025). Reading the table once, in order, is cheaper than 40,575 separate index lookups, each followed by a jump into the table. The index changed the plan — it did not make it faster.
- **`ix_orderline_product` is useless *for the dashboard*,** because `product` is reached through its primary key. For a query that filters on `product_id`, it is used and gives a 6× speedup. "Useless for this query" is the right conclusion; "useless index" is not.
- **A function on the column defeats the index:** `WHERE date(ordered_on) = '2026-02-14'` still does `SCAN o` with the index in place, and stays at about 9 ms.

<a id="task-3"></a>
## Task 3 — The injection drill

**Proves:** [LG5](#lg5)

[`injection_demo.py`](injection_demo.py) — output in [`injection-results.txt`](injection-results.txt):

```text
normal   : [(1, 'Customer 1')]
apostrophe: crashed with near "Brien": syntax error
injected : [(1, 'Customer 1'), (2, 'Customer 2'), (3, 'Customer 3')] ...
           rows returned: 2000
safe     : []
safe     : []
```

- **The apostrophe crash:** the name `O'Brien` closes the string early, and the rest becomes broken SQL.
- **The payload:** `' OR '1'='1` turns the filter into "or true" and returns **all 2,000 customers**.
- **The fix:** with `?` and a bound tuple, both are just data — no crash, no leak.

**Why escaping `'` by hand is not a real fix, but bound parameters are:**
Escaping only covers the one case you thought of. It does nothing for numbers (`WHERE id = 1 OR 1=1` has no quote to escape), nothing for names of tables or columns, and it can break with other encodings or a different database's quoting rules.
It also makes *every* developer responsible for getting it right *every* time. With bound parameters, the value is sent separately from the SQL, so the database never reads it as code — the database is responsible, and there is nothing to forget.

<a id="task-4"></a>
## Task 4 — One query, from algebra to plan

The dashboard query from Task 1:

```text
τ revenue DESC (
  γ city; COUNT(DISTINCT customer_id) → customers, SUM(qty · price) → revenue (
    σ ordered_on ≥ '2025-01-01' ∧ ordered_on < '2026-01-01' (
      customer ⋈ customer_id orders ⋈ order_id order_line ⋈ product_id product
    )
  )
)
```

| algebra | SQL |
|---|---|
| ⋈ (three joins) | `JOIN … ON` |
| σ (date range) | `WHERE` |
| γ (group by city, two aggregates) | `GROUP BY c.city` + `COUNT(DISTINCT …)`, `SUM(…)` |
| τ (sort) | `ORDER BY revenue DESC` |

The plan matches the algebra: the engine evaluates the joins first (`SCAN ol` + three `SEARCH`es), then the grouping and distinct count (temp B-trees), and sorts last.
τ is not part of classic relational algebra (relations are sets and have no order) — it is an extension for `ORDER BY`.

## Reflection 3

[Reflection 3](../Reflections/ref03.md)
