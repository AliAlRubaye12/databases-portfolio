# Reflection 1 — Setting up and first local database

Module: [Module 1 — Introduction and Local-First](../Module01/README.md)

## Take-away

**What do you want to remember? What would be your advice to your past self?**

A small app does not need a server. 

## What was good?

**Which measurement, circuit, or explanation worked well — and why?**

Measuring instead of believing. The file size, the row count, and the `.timer` numbers proved the "no server needed" idea better than any slide.
Playing SQL Island was also a good start — I finished the whole game, and it made `SELECT`, `WHERE`, and `UPDATE` feel normal.

## What was difficult?

**Where did you struggle? What was the root cause?**

The setup. `uv` picked Python 3.15 by itself, and then `datasette` failed to install.
The root cause: Python 3.15 was too new, so one package (`pyyaml`) had no ready-made version for it. Switching to Python 3.14 fixed it.

## Exploration and show stoppers

**Was there any good or fun “struggling” or exploration? Anything where you should reach out to peers or instructors?**

Learning the difference between *commit* (save on my laptop) and *push* (upload to GitHub).
Also: pasting many lines into the `sqlite3` shell can break, so I put my commands in a file and ran it with `.read`.

## Interaction with peers and instructors

**Who did you work with, what did you learn from them, and what did you give back?**

I added the instructor (ulno) as a collaborator on my portfolio.
<add your pod mates here, and one thing you learned from them>

## How did you verify AI suggestions?

**What did you ask an AI, and how did you check the answer against a datasheet, a measurement, a packet capture, or a live test? Where was it wrong?**

I asked Claude for a query: the average spindle load per machine "overnight".
The query ran, but it only looked at 18:00 to midnight and missed the hours after midnight. I found this by counting the rows each filter keeps.
With the full night, a different machine came out on top. So: a query that runs is not automatically right.

## Help and extra work

**Who helped you, and was it valuable? Who did you help? Did you present, implement, make a PR, or fix something crucial for the class?**

Claude helped me install the tools, set up the repository, and run the labs — very useful, but I had to check its work.
Extra: I wrote down the Python 3.15 problem and its fix, so pod mates with the same error can solve it quickly.
