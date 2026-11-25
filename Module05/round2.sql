-- Round 2: cause the three anomalies on purpose. Run from the repo root with
--   sqlite3 ":memory:" ".read Module05/round2.sql"
.mode column
.headers on
CREATE TABLE flat5(
  job_id INTEGER, machine_id TEXT, site TEXT,
  technician TEXT, part_no TEXT, part_price REAL
);
INSERT INTO flat5 VALUES
  (1,'cnc-01','Gütersloh','tech-0','P-0001',6.00),
  (1,'cnc-01','Gütersloh','tech-0','P-0002',7.00),
  (2,'cnc-02','Gütersloh','tech-1','P-0001',6.00),
  (2,'cnc-02','Gütersloh','tech-1','P-0003',8.50),
  (3,'cnc-01','Gütersloh','tech-0','P-0003',8.50);

.print == 1. UPDATE anomaly: move cnc-01 to Bielefeld
UPDATE flat5 SET site = 'Bielefeld' WHERE machine_id = 'cnc-01';
SELECT changes() AS rows_touched;
.print -- a second session that only fixes "the row it is looking at" leaves the fact split:
UPDATE flat5 SET site = 'Gütersloh' WHERE job_id = 3;
SELECT machine_id, GROUP_CONCAT(DISTINCT site) AS sites_now FROM flat5 WHERE machine_id = 'cnc-01';

.print
.print == 2. INSERT anomaly: a new part P-0004 that no job has used yet
INSERT INTO flat5(part_no, part_price) VALUES ('P-0004', 9.25);
SELECT * FROM flat5 WHERE part_no = 'P-0004';
.print -- the part "exists" only as a half-empty fake job row with job_id NULL

.print
.print == 3. DELETE anomaly: delete job 1, the last job that used P-0002
DELETE FROM flat5 WHERE job_id = 1;
SELECT COUNT(*) AS rows_still_knowing_price_of_P_0002 FROM flat5 WHERE part_no = 'P-0002';
