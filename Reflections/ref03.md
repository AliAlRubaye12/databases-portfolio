# Reflection 3 — Query plans, indexes, and injection

Module: [Module 3 — LLM-Assisted SQL & Query Profiling](../Module03/README.md)

## Take-away

**What do you want to remember? What would be your advice to your past self?**

An index is not magic. It made one query 18× faster and another one 9× slower.
Advice to my past self: look at `EXPLAIN QUERY PLAN` first, then measure — never just add indexes and hope.

## What was good?

**Which measurement, circuit, or explanation worked well — and why?**

The benchmark script. It ran every query 5 times after each new index, so I could see plan and time change side by side.
The injection demo was also clear: one apostrophe crashed the query, and `' OR '1'='1` returned all 2,000 customers.

## What was difficult?

**Where did you struggle? What was the root cause?**

Understanding why an index can make a query slower. The root cause: the dashboard reads two thirds of all order lines,
and jumping through an index 40,575 times is slower than reading the table once from start to end.

## Exploration and show stoppers

**Was there any good or fun “struggling” or exploration? Anything where you should reach out to peers or instructors?**

`LIKE 'Bei%'` does not use the index, but `GLOB 'Bei*'` does — because `LIKE` ignores upper/lower case.
Also: SQLite allows a `SELECT` alias in `WHERE`, but PostgreSQL does not. Good question for `#sql-questions`.

## Interaction with peers and instructors

**Who did you work with, what did you learn from them, and what did you give back?**

<add your pod mates and the neighbouring pod from Task C here>

## How did you verify AI suggestions?

**What did you ask an AI, and how did you check the answer against a datasheet, a measurement, a packet capture, or a live test? Where was it wrong?**

Claude wrote the dashboard query. I compared it with the reference query using `EXCEPT` — same result.
But it used `strftime('%Y', …)`, which can never use an index on the date.
Claude also suggested three indexes. I tested each one alone: one helped another query, one did nothing for the dashboard, and one made it 9× slower.
And Claude's first guess for why revenue differs per city was wrong — a query showed the real reason (the quantity, not the price).

## Help and extra work

**Who helped you, and was it valuable? Who did you help? Did you present, implement, make a PR, or fix something crucial for the class?**

Claude helped me write the scripts and run the tests — useful, but I checked every claim with a query.
Extra: the `bench.py` script, so the whole benchmark runs again with one command.
