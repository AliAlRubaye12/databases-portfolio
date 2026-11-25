-- Round 1: test candidate functional dependencies X -> Y with data.
-- X -> Y holds in a table when no X value has more than one Y value (max_y_per_x = 1).
-- Run from the repo root with
--   sqlite3 Module05/normalize.db ".read Module05/fd_check.sql"
.mode column
.headers on

CREATE TEMP TABLE flat5(job_id INTEGER, machine_id TEXT, site TEXT, technician TEXT, part_no TEXT, part_price REAL);
INSERT INTO flat5 VALUES
  (1,'cnc-01','Gütersloh','tech-0','P-0001',6.00), (1,'cnc-01','Gütersloh','tech-0','P-0002',7.00),
  (2,'cnc-02','Gütersloh','tech-1','P-0001',6.00), (2,'cnc-02','Gütersloh','tech-1','P-0003',8.50),
  (3,'cnc-01','Gütersloh','tech-0','P-0003',8.50);

.print == candidate FDs: max number of Y values per X, in the 5 rows and in the 200,000 rows
SELECT 'job_id -> machine_id' AS fd,
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT machine_id) c FROM flat5 GROUP BY job_id)) AS in_5_rows,
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT machine_id) c FROM flat_jobpart GROUP BY job_id)) AS in_200k
UNION ALL SELECT 'job_id -> technician',
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT technician) c FROM flat5 GROUP BY job_id)),
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT technician) c FROM flat_jobpart GROUP BY job_id))
UNION ALL SELECT 'machine_id -> site',
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT site) c FROM flat5 GROUP BY machine_id)),
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT site) c FROM flat_jobpart GROUP BY machine_id))
UNION ALL SELECT 'part_no -> part_price',
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT part_price) c FROM flat5 GROUP BY part_no)),
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT part_price) c FROM flat_jobpart GROUP BY part_no))
UNION ALL SELECT 'technician -> machine_id  (accident?)',
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT machine_id) c FROM flat5 GROUP BY technician)),
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT machine_id) c FROM flat_jobpart GROUP BY technician))
UNION ALL SELECT 'part_price -> part_no  (accident?)',
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT part_no) c FROM flat5 GROUP BY part_price)),
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT part_no) c FROM flat_jobpart GROUP BY part_price))
UNION ALL SELECT '{} -> site  (accident?)',
  (SELECT COUNT(DISTINCT site) FROM flat5),
  (SELECT COUNT(DISTINCT site) FROM flat_jobpart)
UNION ALL SELECT 'job_id -> part_no  (should fail)',
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT part_no) c FROM flat5 GROUP BY job_id)),
  (SELECT MAX(c) FROM (SELECT COUNT(DISTINCT part_no) c FROM flat_jobpart GROUP BY job_id));

.print
.print == candidate key (job_id, part_no): unique in both tables?
SELECT (SELECT COUNT(*) = COUNT(DISTINCT job_id || '|' || part_no) FROM flat5)       AS unique_in_5_rows,
       (SELECT COUNT(*) = COUNT(DISTINCT job_id || '|' || part_no) FROM flat_jobpart) AS unique_in_200k;
