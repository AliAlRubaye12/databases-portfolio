-- Task 2: idempotent edge ingestion with UPSERT. Run from the repo root with
--   sqlite3 Module04/edge.db ".read Module04/task2.sql"
PRAGMA foreign_keys = ON;
.mode column
.headers on

-- Make (sensor_id, ts) a genuine natural key so replays collide:
CREATE UNIQUE INDEX IF NOT EXISTS ux_reading_sensor_ts ON reading(sensor_id, ts);

.print == before the replay
SELECT sensor_id, ts, value FROM reading WHERE sensor_id = 1;

-- Replay-safe ingest: insert, or update if the exact reading already exists.
INSERT INTO reading(sensor_id, ts, value, interval_s)
VALUES (1,'2026-03-01 08:00:00', 41.7, 1)          -- same key, corrected value (sensor retried)
ON CONFLICT(sensor_id, ts) DO UPDATE SET value = excluded.value;

.print
.print == after the replay: still exactly one row for that key, with the corrected value
SELECT sensor_id, ts, value FROM reading WHERE sensor_id = 1;

.print
.print == without ON CONFLICT the same replay is simply rejected:
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (1,'2026-03-01 08:00:00', 41.7, 1);
