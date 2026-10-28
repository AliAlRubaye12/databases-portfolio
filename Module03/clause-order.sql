-- Workstream 2: written vs. evaluated clause order — test the claims instead of trusting them.
-- Run from the repo root with
--   sqlite3 Module03/warehouse.db ".read Module03/clause-order.sql"
.mode column
.headers on

.print == 1. a SELECT alias used in WHERE (standard SQL rejects this; does SQLite?)
SELECT order_id, qty * 2 AS double_qty FROM order_line WHERE double_qty > 7 LIMIT 3;

.print
.print == 2. an aggregate alias used in WHERE (WHERE runs before GROUP BY, so this must fail)
SELECT order_id, SUM(qty) AS total FROM order_line WHERE total > 10 GROUP BY order_id LIMIT 3;

.print
.print == 3. the fix: filter groups in HAVING, which runs after GROUP BY
SELECT order_id, SUM(qty) AS total FROM order_line GROUP BY order_id HAVING total > 10 LIMIT 3;
