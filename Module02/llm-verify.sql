-- Task A: verify LLM answers against legacy.db.
-- Run from the repo root with
--   sqlite3 Module02/legacy.db ".read Module02/llm-verify.sql"
.mode column
.headers on

.print == Q3 natural vs surrogate key: what if machine_name is the key and a machine is renamed?
.print -- orphan jobs before the rename:
SELECT COUNT(*) AS orphan_jobs FROM maint_job
WHERE machine_name NOT IN (SELECT machine_name FROM machine);
BEGIN;
UPDATE machine SET machine_name = 'CNC-01-Hall-B' WHERE machine_name = 'cnc-01';
.print -- orphan jobs after renaming cnc-01 (rolled back afterwards):
SELECT COUNT(*) AS orphan_jobs FROM maint_job
WHERE machine_name NOT IN (SELECT machine_name FROM machine);
ROLLBACK;

.print
.print == Q4 comma list breaks 1NF: can SQL answer "which jobs used P-1002?"
.print -- equality on the list misses it:
SELECT job_id FROM maint_job WHERE parts_used = 'P-1002';
.print -- LIKE finds it:
SELECT job_id, parts_used FROM maint_job WHERE parts_used LIKE '%P-1002%';
.print -- ...but the same pattern would also match a future part P-10021 (simulated, rolled back):
BEGIN;
INSERT INTO maint_job VALUES (5, 'cnc-02', 'Klaas', '2026-03-10', 'P-10021');
SELECT job_id, parts_used FROM maint_job WHERE parts_used LIKE '%P-1002%';
ROLLBACK;

.print
.print == Q5 entity or attribute: is site worth its own table?
SELECT site, COUNT(*) AS machines FROM machine GROUP BY site;

.print
.print == Q7 foreign keys: does SQLite enforce them by default?
PRAGMA foreign_keys;
