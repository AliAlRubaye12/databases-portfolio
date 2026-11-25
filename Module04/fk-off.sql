-- What silently breaks when a tool forgets PRAGMA foreign_keys = ON?
-- Run from the repo root with
--   sqlite3 Module04/edge.db ".read Module04/fk-off.sql"
.mode column
.headers on
.print == foreign_keys on this connection:
PRAGMA foreign_keys;
.print == the same orphan insert that Task 1 rejected - inside a transaction we roll back:
BEGIN;
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (99,'2026-03-01 08:00:03', 40, 1);
SELECT reading_id, sensor_id, ts FROM reading WHERE sensor_id = 99;
ROLLBACK;
