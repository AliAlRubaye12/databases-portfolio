# Reflection 6a — The right engine for the report

Module: [Module 6a — The Analytical Engine (DuckDB)](../Module06a/README.md)

## Take-away

**What do you want to remember? What would be your advice to your past self?**

There is no "best database" — DuckDB was 149× faster for the big report and 480× slower for single inserts.
Advice to my past self: always check that both engines give the same answer before comparing their speed.

## What was good?

**Which measurement, circuit, or explanation worked well — and why?**

The file sizes: 113 MB in SQLite, 2.4 MB as Parquet, with exactly the same rows and the same total.
And `EXPLAIN ANALYZE` showed why: DuckDB only read 4 of the 7 columns.

## What was difficult?

**Where did you struggle? What was the root cause?**

The workbook's monthly query ran in both engines, but SQLite gave a wrong answer (50 rows instead of 1,500).
The root cause: `strftime` takes its arguments in the opposite order in SQLite and DuckDB. The same SQL is not always the same question.

## Exploration and show stoppers

**Was there any good or fun “struggling” or exploration? Anything where you should reach out to peers or instructors?**

An index I added for the one-day query made the dashboard twice as slow, and `ANALYZE` did not help.
Worth telling the instructor: the monthly query in the workbook needs a different spelling for SQLite.

## Interaction with peers and instructors

**Who did you work with, what did you learn from them, and what did you give back?**

<add your pod mates and the discussions with the nearest pod here>

## How did you verify AI suggestions?

**What did you ask an AI, and how did you check the answer against a datasheet, a measurement, a packet capture, or a live test? Where was it wrong?**

An AI assistant warned that the workbook's `strftime` might not work in SQLite. I tested it: 0 months in SQLite instead of 30, so the warning was right.
It also made a mistake: its first test of "two changes that cancel out" used −2 instead of −1, so the check caught it. I fixed the test, and then the check said OK even though two rows were different.

## Help and extra work

**Who helped you, and was it valuable? Who did you help? Did you present, implement, make a PR, or fix something crucial for the class?**

An AI assistant helped me write the scripts and run the tests — useful, but I checked every number.
Extra: the intense track (`refresh.py` with `--check`), stretchers S2 and S3, and finding the `strftime` bug in the workbook.
