# Reflection 4 — Making the database refuse bad data

Module: [Module 4 — Data Integrity, Constraints & Edge Triggers](../Module04/README.md)

## Take-away

**What do you want to remember? What would be your advice to your past self?**

Without constraints, a table accepts anything — even a temperature of 9,000 °C or the word "hot".
Advice to my past self: put the rules in the database, not only in the app, because the database is the one place every tool has to pass through.

## What was good?

**Which measurement, circuit, or explanation worked well — and why?**

Trying to break the table on purpose. Every error message showed exactly which rule stopped which bad row.
UPSERT was also clear: running the same import twice gave 9 rows both times.

## What was difficult?

**Where did you struggle? What was the root cause?**

The small exceptions: `CHECK` lets `NULL` through, and `STRICT` still turns the text `'20'` into a number.
The root cause: SQLite tries to be helpful, so you have to test what a rule really does instead of guessing.

## Exploration and show stoppers

**Was there any good or fun “struggling” or exploration? Anything where you should reach out to peers or instructors?**

Foreign keys are off in every new connection. One connection without `PRAGMA foreign_keys = ON` saved a reading for a sensor that does not exist — with no error.
Also: the audit trigger logs an update even when the value did not change (1.4 → 1.4).

## Interaction with peers and instructors

**Who did you work with, what did you learn from them, and what did you give back?**

<add your pod mates and the pod from Task B here>

## How did you verify AI suggestions?

**What did you ask an AI, and how did you check the answer against a datasheet, a measurement, a packet capture, or a live test? Where was it wrong?**

I asked an AI assistant which trigger can reject a row. The usual answer is "only a `BEFORE` trigger".
I tested it: an `AFTER` trigger with `RAISE(ABORT)` also rejected the row. So that answer was wrong for SQLite.

## Help and extra work

**Who helped you, and was it valuable? Who did you help? Did you present, implement, make a PR, or fix something crucial for the class?**

An AI assistant helped me write the scripts and run the tests — useful, but I checked every claim by running it.
Extra: the stretcher task (BEFORE vs AFTER triggers), a Windows version of the `chmod` steps, and a script that measures the trigger cost.
