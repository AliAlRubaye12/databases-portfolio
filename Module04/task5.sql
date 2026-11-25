-- Task 5 (stretcher): BEFORE vs AFTER, and a rule a CHECK cannot express.
-- Runs on a scratch copy of the schema:
--   sqlite3 ":memory:" ".read Module04/task5.sql"
.read Module04/setup.sql
.mode column
.headers on
.bail off
CREATE TABLE alarm(alarm_id INTEGER PRIMARY KEY, sensor_id INTEGER NOT NULL, ts TEXT NOT NULL,
                   value REAL NOT NULL, reason TEXT NOT NULL, reading_id INTEGER) STRICT;
INSERT INTO sensor VALUES (1,'cnc-01','temp_c','degC'), (2,'cnc-01','vib_rms','mm/s');

.print == 1. alarm as a BEFORE INSERT trigger: which reading_id does it see?
CREATE TRIGGER trg_before BEFORE INSERT ON reading FOR EACH ROW
WHEN NEW.value > 2.0 AND (SELECT metric FROM sensor WHERE sensor_id = NEW.sensor_id) = 'vib_rms'
BEGIN
    INSERT INTO alarm(sensor_id, ts, value, reason, reading_id)
    VALUES (NEW.sensor_id, NEW.ts, NEW.value, 'BEFORE: vibration over 2.0', NEW.reading_id);
END;
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (2,'2026-03-01 09:00:00', 2.7, 1);
SELECT a.reason, a.reading_id AS id_seen_by_trigger, r.reading_id AS real_id
FROM alarm a JOIN reading r ON r.ts = a.ts;

.print
.print == 2. BEFORE trigger, then the row fails a constraint (interval_s = 0): is the alarm kept?
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (2,'2026-03-01 09:00:01', 2.9, 0);
SELECT COUNT(*) AS alarms_after_failed_insert FROM alarm;

.print
.print == 3. a rule a CHECK cannot express: readings must arrive in time order per sensor
CREATE TRIGGER trg_in_order BEFORE INSERT ON reading FOR EACH ROW
WHEN NEW.ts <= (SELECT MAX(ts) FROM reading WHERE sensor_id = NEW.sensor_id)
BEGIN
    SELECT RAISE(ABORT, 'reading is older than the latest one for this sensor');
END;
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (2,'2026-03-01 09:00:05', 1.1, 1);
.print -- an old reading arrives late:
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (2,'2026-03-01 08:59:59', 1.0, 1);
SELECT sensor_id, ts, value FROM reading ORDER BY ts;
