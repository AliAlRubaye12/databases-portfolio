# Module 1 — Introduction and Local-First

Course workbook: [Module 1 — Introduction and Local-First](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/01-introduction-and-local-first.md)

**What I plan to explore:** <one line in your own words — e.g. what you want to build or learn in this class>

## Learning Goals

<a id="lg1"></a>
### LG1 — `class`

Explain how this class works — the CBL/PBL philosophy, the portfolio-based project work assessment, and the "moving bar" of a first-time course.

**Evidence:** [Personal profile](#task-personal-profile)

<a id="lg2"></a>
### LG2 — `portfolio`

Set up your personal GitHub portfolio from the course template, with a clean first commit and a `.gitignore` that keeps databases and secrets out of Git.

**Evidence:** [Task 1 — Portfolio](#task-1)

<a id="lg3"></a>
### LG3 — `toolchain`

Set up the entire toolchain reproducibly with uv — one fixed Python plus SQLite, DuckDB, Datasette, and more — on Windows, macOS, or Linux, and verify it.

**Evidence:** [Task 3 — Toolchain](#task-3)

<a id="lg4"></a>
### LG4 — `embedded`

Explain — with a measurement, not a slide — the difference between an embedded database and a client/server database, and why most local apps should not run a server.

**Evidence:** [Discovery](#task-discovery)

<a id="lg5"></a>
### LG5 — `sqlite`

Load real rows into SQLite and query them from Python using bound parameters.

**Evidence:** _(later studio task)_

<a id="lg6"></a>
### LG6 — `verify-ai`

Take a first LLM-generated query, run it, and begin the habit that defines this course: verify before you trust.

**Evidence:** [Task 3 — what I verified](#task-3), _(later studio task)_

<a id="task-personal-profile"></a>
## Personal profile

**Proves:** [LG1](#lg1)

My answers from the "Who are U?" round:

- Programming experience and languages:
- Prior SQL:
- Databases I have used:
- Python:
- Command line:
- Git / GitHub:
- Built a web app or run a server:
- **My expectations from this class:**

## My Task Pod

- <pod mate 1>, [portfolio](https://github.com/USERNAME/databases-portfolio)
- <pod mate 2>, [portfolio](https://github.com/USERNAME/databases-portfolio)

Links: [syllabus](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/syllabus.md) · [this module in the workbook](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/01-introduction-and-local-first.md) · [my reflection](../Reflections/ref01.md)

<a id="task-discovery"></a>
## Discovery — Embedded vs. Client/Server

**Proves:** [LG4](#lg4)

_Our pod's own brainstorm before the reveal:_

| | Embedded | Client/server |
|---|---|---|
| Our name for it | | |
| Advantage | | |
| Cost | | |
| Example engines | | |

What our jigsaw found that the instructor's table missed:

<a id="task-1"></a>
## Task 1 — Portfolio

**Proves:** [LG2](#lg2)

- Repository created from [iotempire/iot-portfolio-template](https://github.com/iotempire/iot-portfolio-template) with **Use this template** (not a fork), so it starts with one clean commit and no upstream link.
- Cloned with `gh repo clone`, signed in over HTTPS with `gh auth login` (no SSH keys).
- The template had **no `.gitignore`**, so I added one: [`.gitignore`](../.gitignore). Besides the required entries, it also ignores SQLite's `-wal`/`-shm` side files and `*.sqlite`/`*.sqlite3`.
- Instructor added as collaborator: <yes / pending>

<a id="task-2"></a>
## Task 2 — Git & Markdown

**Proves:** [LG2](#lg2)

Small commits, each saying what changed — see the [commit history](https://github.com/AliAlRubaye12/databases-portfolio/commits/main).

Who did what in our pod:

<a id="task-3"></a>
## Task 3 — Toolchain with uv

**Proves:** [LG3](#lg3), [LG6](#lg6)

Installed on Windows 10 with winget: `gh`, `uv`, `sqlite3`. Tools via `uv tool install`: `litecli`, `datasette`, `sqlite-utils`.
The project pins Python in [`.python-version`](../.python-version) and locks every library in [`uv.lock`](../uv.lock).

Output of `uv run uv-check.py` ([script](../uv-check.py)):

```text
uv-managed Python: C:\Users\ali\Downloads\zash\databases-portfolio\.venv\Scripts\python.exe
python             3.14.10
sqlite (stdlib)    3.53.1
duckdb             2.0.0
datasette          0.65.5
sqlite-utils       4.2.1
pydantic           2.14.1
sqlalchemy         2.1.6
```

Command-line `sqlite3 --version`: `3.53.4`.

**What went wrong and how I verified the fix:**

- uv's default was the newest Python, **3.15**. `datasette` depends on `pyyaml`, which had no prebuilt Windows wheel for 3.15, so uv tried to compile it and failed (*"Microsoft Visual C++ 14.0 or greater is required"*). This is exactly the case the workbook warns about.
- Fix: `uv python install 3.14`, then `uv init --python 3.14` and `uv python pin 3.14`. With 3.14 every package installed from a prebuilt wheel.
- Versions differ slightly from the ones the course was tested with (for example `duckdb 2.0.0` instead of `1.5.6`), because `uv add` takes the newest compatible release. `uv.lock` records the exact versions, so a reviewer gets the same environment.

## Reflection 1

[Reflection 1](../Reflections/ref01.md)
