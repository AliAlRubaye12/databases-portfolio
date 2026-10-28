-- Task A: plan safari on Module02/legacy.db.
-- Predictions (written before running):
--   Q1 technician = 'Beier'      -> SCAN  (no index on technician)
--   Q2 machine_name = 'cnc-02'   -> SCAN  (no primary key, no index)
--   Q3 technician LIKE '%ei%'    -> SCAN
--   after ix_job_tech: Q1 -> SEARCH, Q2 -> SCAN (other table), Q3 -> SCAN (leading wildcard)
-- Run from the repo root with
--   sqlite3 Module02/legacy.db ".read Module03/safari.sql"
-- The index is dropped at the end, so Module 2's results stay reproducible.

.print == BEFORE the index
.print -- Q1
EXPLAIN QUERY PLAN SELECT * FROM maint_job WHERE technician = 'Beier';
.print -- Q2
EXPLAIN QUERY PLAN SELECT * FROM machine WHERE machine_name = 'cnc-02';
.print -- Q3
EXPLAIN QUERY PLAN SELECT * FROM maint_job WHERE technician LIKE '%ei%';

CREATE INDEX ix_job_tech ON maint_job(technician);

.print
.print == AFTER CREATE INDEX ix_job_tech ON maint_job(technician)
.print -- Q1
EXPLAIN QUERY PLAN SELECT * FROM maint_job WHERE technician = 'Beier';
.print -- Q2
EXPLAIN QUERY PLAN SELECT * FROM machine WHERE machine_name = 'cnc-02';
.print -- Q3
EXPLAIN QUERY PLAN SELECT * FROM maint_job WHERE technician LIKE '%ei%';

.print
.print == BREAK IT: WHEREs that defeat the index
.print -- function around the column
EXPLAIN QUERY PLAN SELECT * FROM maint_job WHERE lower(technician) = 'beier';
.print -- prefix LIKE without wildcard at the start (LIKE is case-insensitive, so still no index)
EXPLAIN QUERY PLAN SELECT * FROM maint_job WHERE technician LIKE 'Bei%';
.print -- the same prefix with GLOB (case-sensitive) can use the index
EXPLAIN QUERY PLAN SELECT * FROM maint_job WHERE technician GLOB 'Bei*';
.print -- only the indexed column is needed: covering index
EXPLAIN QUERY PLAN SELECT technician FROM maint_job WHERE technician = 'Beier';

DROP INDEX ix_job_tech;
