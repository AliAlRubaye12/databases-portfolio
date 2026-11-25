# Reflection 6b — Which data lives where

Module: [Module 6b — Polyglot Persistence & the Decision](../Module06b/README.md)

## Take-away

**What do you want to remember? What would be your advice to your past self?**

Pick the engine per workload, and write down the number that made you pick it.
Advice to my past self: a "different engine" is sometimes the same engine used differently — Python's `shelve` turned out to be SQLite underneath.

## What was good?

**Which measurement, circuit, or explanation worked well — and why?**

The two query plans for JSON: `json_extract(...)` used the index, `->>` scanned the whole table — same question, same 334 rows.
Seeing it in the plan made it clear that an index only matches the exact expression.

## What was difficult?

**Where did you struggle? What was the root cause?**

ACID, BASE and CAP are easy to say and hard to connect to real things.
It helped to tie each word to something I ran: the uncommitted change nobody could see (ACID), the Parquet copy that is a day behind (BASE).

## Exploration and show stoppers

**Was there any good or fun “struggling” or exploration? Anything where you should reach out to peers or instructors?**

The lost update: two writers both added +1, and the counter only went up by one. Locking alone does not stop that — doing the +1 inside the SQL does.

## Interaction with peers and instructors

**Who did you work with, what did you learn from them, and what did you give back?**

<add your pod mates, the server session in class, and the pod that questioned your decision record>

## How did you verify AI suggestions?

**What did you ask an AI, and how did you check the answer against a datasheet, a measurement, a packet capture, or a live test? Where was it wrong?**

I used an AI assistant to write the benchmark scripts. Its first two-writer script crashed at the end on Windows, because one connection was still open — I had to fix it before the results counted.
The key-value numbers looked strange, so I checked which backend `shelve` uses: `dbm.sqlite3`. Without that check, I would have compared "two engines" that were really one.

## Help and extra work

**Who helped you, and was it valuable? Who did you help? Did you present, implement, make a PR, or fix something crucial for the class?**

An AI assistant helped me write the scripts and run the tests — useful, but I checked every number.
Extra: the lost-update demo, the query across sessions in the key-value test, and three project-ticket candidates.
