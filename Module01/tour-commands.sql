-- Task 4 drill: run from the repo root with
--   sqlite3 Module01/tour.db ".read Module01/tour-commands.sql"
DROP TABLE IF EXISTS reading;
CREATE TABLE reading(machine TEXT, vib REAL);
INSERT INTO reading VALUES ('cnc-01', 1.2), ('cnc-02', 2.4), ('cnc-01', 0.9);

-- capture the session into a file
.output Module01/shell-tour.txt
.print -- .tables
.tables
.print
.print -- .schema reading
.schema reading
.print
.print -- query, aligned columns with headers, timed
.mode column
.headers on
.timer on
SELECT machine, max(vib) AS peak FROM reading GROUP BY machine;
.timer off

-- the whole schema + data as SQL
.output Module01/tour.sql
.dump

-- back to the screen
.output stdout
