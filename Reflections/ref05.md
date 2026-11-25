# Reflection 5 — Normalize or copy?

Module: [Module 5 — Normalization vs. Denormalization](../Module05/README.md)

## Take-away

**What do you want to remember? What would be your advice to your past self?**

"One table is faster" is not always true. On 200,000 rows, the copied report table was even *slower* than the normal join while it had its index.
Advice to my past self: measure first, and always ask *which* cost a copy removes.

## What was good?

**Which measurement, circuit, or explanation worked well — and why?**

Counting rows touched: changing one machine's site touched 1 row in the clean tables and 4,000 rows in the copy.
That one number explains the whole trade-off better than the milliseconds.

## What was difficult?

**Where did you struggle? What was the root cause?**

Telling real rules from accidents. In five rows it looked like "tech-0 always works on cnc-01", but in 200,000 rows tech-0 works on 50 machines.
The root cause: a few rows can make anything look like a rule. Data can only prove a rule wrong, never prove it right.

## Exploration and show stoppers

**Was there any good or fun “struggling” or exploration? Anything where you should reach out to peers or instructors?**

A plan that lied: after dropping an index, Python still showed the old plan, because it had cached the statement. The `sqlite3` shell showed the real plan.
DuckDB ran the normal query 7× faster than SQLite's best — maybe a faster engine is better than making copies.

## Interaction with peers and instructors

**Who did you work with, what did you learn from them, and what did you give back?**

<add your pod mates and the exchanges with the nearest pod here>

## How did you verify AI suggestions?

**What did you ask an AI, and how did you check the answer against a datasheet, a measurement, a packet capture, or a live test? Where was it wrong?**

I worked out the list of functional dependencies with an AI assistant, then tested every one with a query on 5 rows and on 200,000 rows.
Two "rules" that looked true in 5 rows broke on the big table. One still held, but only by accident of how the data was made.

## Help and extra work

**Who helped you, and was it valuable? Who did you help? Did you present, implement, make a PR, or fix something crucial for the class?**

An AI assistant helped me write the scripts and run the tests — useful, but I checked every claim by running it.
Extra: the optional six-way join test and the DuckDB comparison.
