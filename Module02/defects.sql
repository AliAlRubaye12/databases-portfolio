-- Task 2: prove the integrity defects with queries.
-- Run from the repo root with
--   sqlite3 Module02/legacy.db ".read Module02/defects.sql"
.mode column
.headers on
.timer on

.print == Defect 1: orphan maintenance jobs (machine_name not in machine)
SELECT m.job_id, m.machine_name
FROM maint_job m
LEFT JOIN machine x ON m.machine_name = x.machine_name
WHERE x.machine_name IS NULL;

.print
.print == Defect 2: duplicate natural keys in part
SELECT part_no, COUNT(*) AS copies
FROM part GROUP BY part_no HAVING COUNT(*) > 1;

.print
.print == Defect 3: unit_price stored as text - a numeric comparison fails silently
SELECT part_no, unit_price FROM part WHERE unit_price < '15';
.print -- the same question asked numerically:
SELECT part_no, unit_price FROM part WHERE CAST(unit_price AS REAL) < 15;

.print
.print == Defect 4: installed dates that are not dates
SELECT machine_name, installed FROM machine
WHERE installed NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]';

.print
.print == Defect 5: the m:n list only "joins" when it holds exactly one part
SELECT j.job_id, p.description
FROM maint_job j
JOIN part p ON p.part_no = j.parts_used;
.print -- jobs that silently disappeared from that join:
SELECT job_id, parts_used FROM maint_job
WHERE job_id NOT IN (SELECT j.job_id FROM maint_job j JOIN part p ON p.part_no = j.parts_used);
