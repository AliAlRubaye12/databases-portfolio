# Reflection 2 — Reading an old database

Module: [Module 2 — Data Contracts & Legacy Schemas](../Module02/README.md)

## Take-away

**What do you want to remember? What would be your advice to your past self?**

An old database can look fine and still be full of mistakes. Don't guess — run a query and count.
Advice to my past self: before trusting a table, check `COUNT(*)` against `COUNT(DISTINCT …)` to see if a "key" is really unique.

## What was good?

**Which measurement, circuit, or explanation worked well — and why?**

The defect queries. Each one showed a real problem with a real result.
My favourite: prices were saved as text, so `'9.90' < '15'` was false and the cheapest part went missing.
Drawing the ER diagrams in Mermaid also worked well, because GitHub shows them as pictures.

## What was difficult?

**Where did you struggle? What was the root cause?**

Deciding what is an entity and what is only an attribute or a relationship — for example, why a maintenance job needs its own table.
The root cause: these are new words, and the answer depends on what the business needs to store, not on one fixed rule.

## Exploration and show stoppers

**Was there any good or fun “struggling” or exploration? Anything where you should reach out to peers or instructors?**

Two mistakes can add up: one duplicate part row made a job show up twice in a different query.
Worth telling the instructor: the contract in the workbook drops the `machine_name` column, so the name the shop uses would be lost.

## Interaction with peers and instructors

**Who did you work with, what did you learn from them, and what did you give back?**

I shared our m:n diagram in the class Discord.
The pairing with another pod (Task C) is still to do.

## How did you verify AI suggestions?

**What did you ask an AI, and how did you check the answer against a datasheet, a measurement, a packet capture, or a live test? Where was it wrong?**

I used Claude to help with the lab and to answer the study questions. I checked each answer with a query on `legacy.db`.
It was wrong once: it said job 4 went missing from a join, but job 4 has no parts, so that was expected.
Checking also showed that SQLite does not turn on foreign keys by default (`PRAGMA foreign_keys` was `0`).

## Help and extra work

**Who helped you, and was it valuable? Who did you help? Did you present, implement, make a PR, or fix something crucial for the class?**

Claude helped me set up the files and run the queries — useful, but I had to check its answers.
Extra work: a script that tests every old row against the new contract, and the find about the missing `machine_name`.
