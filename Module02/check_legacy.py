"""Verify the contract: push every legacy row through it and see what it rejects.

Run with:  uv run python Module02/check_legacy.py
Needs Module02/legacy.db (build it with legacy-setup.sql first).
"""
import sqlite3
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import create_engine, insert
from sqlalchemy.exc import IntegrityError

from contract import Machine, MaintenanceJob, metadata, machine_t, part_t, maint_job_t, job_part_t

here = Path(__file__).parent
legacy = sqlite3.connect(here / "legacy.db")

# 1. Application side: Pydantic. Legacy machines have no id, so number them by rowid.
print("== Pydantic: machines")
machine_ids = {}
for rowid, name, serial, site, installed in legacy.execute(
        "SELECT rowid, machine_name, serial_no, site, installed FROM machine"):
    try:
        Machine(machine_id=rowid, serial_no=serial, site=site, installed=installed)
        machine_ids[name] = rowid
        print(f"  ok      {name}")
    except ValidationError as e:
        print(f"  REJECT  {name}: {e.errors()[0]['loc'][0]} - {e.errors()[0]['msg']}")

print("== Pydantic: maintenance jobs")
for job_id, name, tech, done_on, parts in legacy.execute(
        "SELECT job_id, machine_name, technician, done_on, parts_used FROM maint_job"):
    if name not in machine_ids:
        print(f"  REJECT  job {job_id}: machine '{name}' has no machine_id (orphan)")
        continue
    job = MaintenanceJob(job_id=job_id, machine_id=machine_ids[name], technician=tech,
                         done_on=done_on, part_nos=parts.split(",") if parts else [])
    print(f"  ok      job {job_id}: parts {job.part_nos}")

# 2. Database side: SQLAlchemy. Build the corrected schema and insert the legacy parts.
print("== Database: parts into the corrected schema")
engine = create_engine("sqlite://")
metadata.create_all(engine)
for part_no, desc, price in legacy.execute("SELECT part_no, description, unit_price FROM part"):
    try:
        with engine.begin() as conn:
            conn.execute(insert(part_t).values(part_no=part_no, description=desc, unit_price=price))
        print(f"  ok      {part_no}")
    except IntegrityError as e:
        print(f"  REJECT  {part_no}: {e.orig}")

print("== Database: a job_part row pointing at a job that does not exist")
with engine.connect() as conn:
    conn.exec_driver_sql("PRAGMA foreign_keys = ON")    # SQLite leaves FKs off by default
    try:
        conn.execute(insert(job_part_t).values(job_id=99, part_no="P-1001"))
        conn.commit()
        print("  accepted (foreign keys not enforced!)")
    except IntegrityError as e:
        print(f"  REJECT  job 99: {e.orig}")
