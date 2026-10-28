-- Task 7: verify an LLM-generated query.
-- Run from the repo root with
--   sqlite3 Module01/telemetry.db ".read Module01/llm-query.sql"
.mode column
.headers on
.timer on

.print == 1. RUN the generated query as given
SELECT machine, ROUND(AVG(spindle_load), 2) AS avg_load
FROM readings
WHERE time(ts) >= '18:00:00'
GROUP BY machine
ORDER BY avg_load DESC;

.print
.print == 2. PROFILE it
.timer off
EXPLAIN QUERY PLAN
SELECT machine, ROUND(AVG(spindle_load), 2) AS avg_load
FROM readings
WHERE time(ts) >= '18:00:00'
GROUP BY machine
ORDER BY avg_load DESC;

.print
.print == 3a. BREAK it: which hours does each filter actually keep?
SELECT 'time(ts) >= 18:00' AS filter, MIN(time(ts)) AS first, MAX(time(ts)) AS last, COUNT(*) AS n
  FROM readings WHERE time(ts) >= '18:00:00'
UNION ALL
SELECT 'overnight 18:00-06:00', NULL, NULL, COUNT(*)
  FROM readings WHERE time(ts) >= '18:00:00' OR time(ts) < '06:00:00'
UNION ALL
SELECT 'ts > 2026-01-05 18:00', MIN(ts), MAX(ts), COUNT(*)
  FROM readings WHERE ts > '2026-01-05 18:00:00'
UNION ALL
SELECT 'sloppy LIKE %18%', NULL, NULL, COUNT(*)
  FROM readings WHERE ts LIKE '%18%';

.print
.print == 3b. what the sloppy LIKE matches that it should not
SELECT ts FROM readings WHERE ts LIKE '%18%' AND time(ts) < '18:00:00' LIMIT 3;

.print
.print == 3c. overnight including after midnight (18:00-06:00)
SELECT machine, ROUND(AVG(spindle_load), 2) AS avg_load
FROM readings
WHERE time(ts) >= '18:00:00' OR time(ts) < '06:00:00'
GROUP BY machine
ORDER BY avg_load DESC;
