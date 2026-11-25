-- Round 5: the price of denormalization — rows touched by one fact change, and storage.
-- Run from the repo root (after race.py built report_jobpart) with
--   sqlite3 Module05/normalize.db ".read Module05/price.sql"
.mode column
.headers on

.print == change one machine's site: 3NF (machine)
.timer on
UPDATE machine        SET site = 'Bielefeld' WHERE machine_id = 'cnc-02';
.timer off
SELECT changes() AS rows_touched_3nf;

.print
.print == the same fact in the report table
.timer on
UPDATE report_jobpart SET site = 'Bielefeld' WHERE machine_id = 'cnc-02';
.timer off
SELECT changes() AS rows_touched_report;

.print
.print == forget the report table, and the two designs disagree:
SELECT (SELECT site FROM machine WHERE machine_id = 'cnc-02') AS site_in_3nf,
       (SELECT GROUP_CONCAT(DISTINCT site) FROM report_wide WHERE machine_id = 'cnc-02') AS site_in_report_wide;

.print
.print == storage (dbstat: bytes of pages per object, indexes included)
SELECT 'normalized (job + job_part + part + machine)' AS design,
       (SELECT SUM(pgsize) FROM dbstat
        WHERE name IN ('job','job_part','part','machine')
           OR name IN (SELECT name FROM sqlite_master WHERE type='index' AND tbl_name IN ('job','job_part','part','machine'))) AS bytes;
SELECT 'denormalized (report_jobpart + ix_report_machine)' AS design,
       (SELECT SUM(pgsize) FROM dbstat WHERE name IN ('report_jobpart','ix_report_machine')) AS bytes;
SELECT 'denormalized, table only' AS design,
       (SELECT SUM(pgsize) FROM dbstat WHERE name = 'report_jobpart') AS bytes;
SELECT 'flat_jobpart (the original, + ix_flat_machine)' AS design,
       (SELECT SUM(pgsize) FROM dbstat WHERE name IN ('flat_jobpart','ix_flat_machine')) AS bytes;
