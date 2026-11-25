-- Task A: what does an unconstrained table accept? Then the same table with constraints.
-- Run from the repo root with
--   sqlite3 ":memory:" ".read Module04/acceptance.sql"
.mode column
.headers on
.bail off

.print == 1. UNCONSTRAINED: everything lands, nothing complains
CREATE TABLE t(sensor_id INTEGER, metric TEXT, value REAL);
INSERT INTO t VALUES (1,'temp_c',9000), (1,'temp_c','hot'), (2,'bogus',-500);
-- my own attempts to break it:
INSERT INTO t VALUES (NULL, NULL, NULL);              -- a completely empty row
INSERT INTO t VALUES ('abc', 'temp_c', 20);           -- text as a sensor id
INSERT INTO t VALUES (1, 'temp_c', 41.5), (1, 'temp_c', 41.5);   -- exact duplicate
INSERT INTO t VALUES (1, 'TEMP_C', 1e308);            -- other spelling, absurd value
INSERT INTO t VALUES (1.5, '', -273.16);              -- fractional id, empty metric, below absolute zero
SELECT rowid, sensor_id, typeof(sensor_id) AS id_type, metric, value, typeof(value) AS value_type FROM t;

.print
.print == 2. CONSTRAINED: the same inserts, one at a time
CREATE TABLE c(
    sensor_id INTEGER NOT NULL,
    metric    TEXT    NOT NULL CHECK (metric IN ('temp_c','vib_rms','spindle_load')),
    value     REAL    NOT NULL CHECK (value BETWEEN -273.15 AND 5000),
    PRIMARY KEY (sensor_id, metric, value)
) STRICT;
.print -- (1,'temp_c',9000)
INSERT INTO c VALUES (1,'temp_c',9000);
.print -- (1,'temp_c','hot')
INSERT INTO c VALUES (1,'temp_c','hot');
.print -- (2,'bogus',-500)
INSERT INTO c VALUES (2,'bogus',-500);
.print -- (NULL,NULL,NULL)
INSERT INTO c VALUES (NULL, NULL, NULL);
.print -- ('abc','temp_c',20)
INSERT INTO c VALUES ('abc', 'temp_c', 20);
.print -- (1,'temp_c',41.5) twice
INSERT INTO c VALUES (1, 'temp_c', 41.5);
INSERT INTO c VALUES (1, 'temp_c', 41.5);
.print -- (1,'TEMP_C',1e308)
INSERT INTO c VALUES (1, 'TEMP_C', 1e308);
.print -- (1.5,'',-273.16)
INSERT INTO c VALUES (1.5, '', -273.16);
.print -- STRICT surprise: the text '20' into a REAL column
INSERT INTO c VALUES (2, 'temp_c', '20');
.print -- ...and an integer 21 into the REAL column
INSERT INTO c VALUES (3, 'temp_c', 21);
SELECT sensor_id, metric, value, typeof(value) AS value_type FROM c;

.print
.print == 3. CHECK and NULL: a CHECK that is NULL counts as passed
CREATE TABLE n(value REAL CHECK (value BETWEEN -273.15 AND 5000)) STRICT;
INSERT INTO n VALUES (NULL);
SELECT COUNT(*) AS null_rows_accepted FROM n;

.print
.print == 4. plausible but wrong: a vibration of 4000 passes the temperature range
INSERT INTO c VALUES (4, 'vib_rms', 4000);
SELECT * FROM c WHERE sensor_id = 4;
