-- Task 1: prove the constraints work. Run from the repo root with
--   sqlite3 Module04/edge.db ".read Module04/task1.sql"
PRAGMA foreign_keys = ON;        -- a new connection: foreign keys are OFF again until this line
.mode column
.headers on
.bail off

.print == valid
INSERT INTO sensor VALUES (1,'cnc-01','temp_c','degC'), (2,'cnc-01','vib_rms','mm/s');
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (1,'2026-03-01 08:00:00', 41.5, 1);
SELECT reading_id, sensor_id, ts, value, interval_s, energy_j FROM reading;

.print
.print == rejected: domain check (impossible temperature)
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (1,'2026-03-01 08:00:01', 9000, 1);
.print == rejected: STRICT type (text into a REAL)
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (1,'2026-03-01 08:00:02', 'hot', 1);
.print == rejected: referential integrity (sensor 99 does not exist)
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (99,'2026-03-01 08:00:03', 40, 1);
.print == rejected: entity integrity (duplicate sensor for the same machine+metric)
INSERT INTO sensor VALUES (3,'cnc-01','temp_c','degC');

.print
.print == the generated column computes on read: a 5-second reading
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (1,'2026-03-01 08:00:05', 42.0, 5);
SELECT reading_id, value, interval_s, energy_j FROM reading;
.print -- and it cannot be written directly:
INSERT INTO reading(sensor_id, ts, value, interval_s, energy_j) VALUES (1,'2026-03-01 08:00:10', 42.0, 1, 999);
DELETE FROM reading WHERE ts = '2026-03-01 08:00:05';
