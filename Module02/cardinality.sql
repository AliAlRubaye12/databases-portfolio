-- Task 1: determine the cardinalities with counts, not guesses.
-- Run from the repo root with
--   sqlite3 Module02/legacy.db ".read Module02/cardinality.sql"
.mode column
.headers on
.timer on

.print == C1. Machine: is machine_name / serial_no unique? (candidate keys)
SELECT COUNT(*) AS rows, COUNT(DISTINCT machine_name) AS names,
       COUNT(DISTINCT serial_no) AS serials
FROM machine;

.print
.print == C2. Part: is part_no unique? (natural key)
SELECT COUNT(*) AS rows, COUNT(DISTINCT part_no) AS part_nos FROM part;

.print
.print == C3. Machine 1:n MaintenanceJob: jobs per machine
SELECT machine_name, COUNT(*) AS jobs FROM maint_job GROUP BY machine_name;

.print
.print == C4. Technician 1:n MaintenanceJob: jobs per technician
SELECT technician, COUNT(*) AS jobs FROM maint_job GROUP BY technician;

.print
.print == C5. MaintenanceJob m:n Part: parts per job (the m:n hiding in a text column)
SELECT job_id, parts_used,
       LENGTH(parts_used) - LENGTH(REPLACE(parts_used, ',', '')) + 1 AS n_parts
FROM maint_job;

.print
.print == C6. ...and jobs per part (the other side of m:n), after splitting the list
WITH RECURSIVE split(job_id, part_no, rest) AS (
    SELECT job_id, NULL, parts_used || ',' FROM maint_job WHERE parts_used IS NOT NULL
    UNION ALL
    SELECT job_id, substr(rest, 1, instr(rest, ',') - 1), substr(rest, instr(rest, ',') + 1)
    FROM split WHERE rest <> ''
)
SELECT part_no, COUNT(*) AS jobs, group_concat(job_id) AS job_ids
FROM split WHERE part_no IS NOT NULL
GROUP BY part_no;
