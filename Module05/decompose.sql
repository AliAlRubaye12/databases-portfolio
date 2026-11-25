-- Round 3: decompose flat_jobpart into 3NF, with foreign keys switched ON.
-- Run from the repo root with
--   sqlite3 Module05/normalize.db ".read Module05/decompose.sql"
PRAGMA foreign_keys = ON;
.mode column
.headers on

DROP TABLE IF EXISTS report_jobpart;
DROP TABLE IF EXISTS job_part;
DROP TABLE IF EXISTS job;
DROP TABLE IF EXISTS part;
DROP TABLE IF EXISTS machine;

CREATE TABLE machine(machine_id TEXT PRIMARY KEY, site TEXT NOT NULL);
CREATE TABLE part(part_no TEXT PRIMARY KEY, part_price REAL NOT NULL);
CREATE TABLE job(job_id INTEGER PRIMARY KEY, machine_id TEXT NOT NULL
                 REFERENCES machine(machine_id), technician TEXT NOT NULL, done_on TEXT NOT NULL);
CREATE TABLE job_part(job_id INTEGER REFERENCES job(job_id),
                      part_no TEXT REFERENCES part(part_no),
                      PRIMARY KEY (job_id, part_no));

INSERT INTO machine SELECT DISTINCT machine_id, site FROM flat_jobpart;
INSERT INTO part    SELECT DISTINCT part_no, CAST(part_price AS REAL) FROM flat_jobpart;
INSERT INTO job     SELECT DISTINCT job_id, machine_id, technician, done_on FROM flat_jobpart;
INSERT INTO job_part SELECT DISTINCT job_id, part_no FROM flat_jobpart;

.print == integrity check: the join must reproduce the row count of the flat table
SELECT (SELECT COUNT(*) FROM flat_jobpart)  AS flat_rows,
       (SELECT COUNT(*) FROM job_part)      AS normalized_rows,
       (SELECT COUNT(*) FROM machine)       AS machines,
       (SELECT COUNT(*) FROM part)          AS parts,
       (SELECT COUNT(*) FROM job)           AS jobs;

.print
.print == and the joined 3NF tables give back exactly the flat rows (both EXCEPTs empty = 0)
SELECT
  (SELECT COUNT(*) FROM (
     SELECT job_id, machine_id, site, technician, part_no, CAST(part_price AS REAL), done_on FROM flat_jobpart
     EXCEPT
     SELECT j.job_id, m.machine_id, m.site, j.technician, p.part_no, p.part_price, j.done_on
     FROM job j JOIN machine m USING(machine_id) JOIN job_part jp USING(job_id) JOIN part p USING(part_no))) AS lost_rows,
  (SELECT COUNT(*) FROM (
     SELECT j.job_id, m.machine_id, m.site, j.technician, p.part_no, p.part_price, j.done_on
     FROM job j JOIN machine m USING(machine_id) JOIN job_part jp USING(job_id) JOIN part p USING(part_no)
     EXCEPT
     SELECT job_id, machine_id, site, technician, part_no, CAST(part_price AS REAL), done_on FROM flat_jobpart)) AS invented_rows;

.print
.print == why does part have 10 rows, not 40? (k only runs 1..10)
SELECT MIN(part_no) AS first_part, MAX(part_no) AS last_part, COUNT(*) AS parts FROM part;

.print
.print == foreign keys were ON during the load; any violations?
PRAGMA foreign_key_check;
.print (no rows above = none)
