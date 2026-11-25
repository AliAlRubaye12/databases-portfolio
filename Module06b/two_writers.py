# Module06b/two_writers.py — run with:  uv run python Module06b/two_writers.py
"""Task 1 fallback (no shared server): two writers on one SQLite file.

1. Two connections, one BEGIN IMMEDIATE: the second writer gets 'database is locked'.
2. The lost update: both read the counter, both write read+1 — one increment disappears.
3. The fix: do the increment inside the database (parts_produced = parts_produced + 1).
"""
import sqlite3
from pathlib import Path

db = Path(__file__).with_name("boundary.db")
db.unlink(missing_ok=True)
setup = sqlite3.connect(db)
setup.executescript("""
CREATE TABLE machine(machine_id INTEGER PRIMARY KEY, site TEXT NOT NULL, parts_produced INTEGER NOT NULL DEFAULT 0);
INSERT INTO machine VALUES (1, 'guetersloh', 0);
""")
setup.close()


def connect():
    # timeout=0: do not wait for a lock, fail at once (the default would wait 5 s, then fail)
    return sqlite3.connect(db, timeout=0, isolation_level=None)


def counter():
    with sqlite3.connect(db) as c:
        value = c.execute("SELECT parts_produced FROM machine WHERE machine_id = 1").fetchone()[0]
    c.close()                      # `with` only ends the transaction; Windows needs the file closed to delete it
    return value


print("== 1. two writers, one row")
a, b = connect(), connect()
a.execute("BEGIN IMMEDIATE")
a.execute("UPDATE machine SET parts_produced = parts_produced + 1 WHERE machine_id = 1")
try:
    b.execute("BEGIN IMMEDIATE")
    print("  writer B: got the lock (unexpected)")
except sqlite3.OperationalError as e:
    print(f"  writer B: {e}")
print(f"  reader while A holds the lock sees: {counter()}  (A has not committed)")
a.execute("COMMIT")
b.execute("BEGIN IMMEDIATE")
b.execute("UPDATE machine SET parts_produced = parts_produced + 1 WHERE machine_id = 1")
b.execute("COMMIT")
print(f"  after A commits, B retries: counter = {counter()}  (expected 2)")

print("\n== 2. the lost update: read in the app, write back read+1")
start = counter()
va = a.execute("SELECT parts_produced FROM machine WHERE machine_id = 1").fetchone()[0]
vb = b.execute("SELECT parts_produced FROM machine WHERE machine_id = 1").fetchone()[0]
a.execute("UPDATE machine SET parts_produced = ? WHERE machine_id = 1", (va + 1,))
b.execute("UPDATE machine SET parts_produced = ? WHERE machine_id = 1", (vb + 1,))
print(f"  both read {va}/{vb}, both wrote +1: counter {start} -> {counter()}  (expected {start + 2})")

print("\n== 3. the fix: let the database do the read-modify-write")
start = counter()
a.execute("UPDATE machine SET parts_produced = parts_produced + 1 WHERE machine_id = 1")
b.execute("UPDATE machine SET parts_produced = parts_produced + 1 WHERE machine_id = 1")
print(f"  counter {start} -> {counter()}  (expected {start + 2})")
a.close(); b.close()
db.unlink()
