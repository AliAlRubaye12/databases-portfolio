-- Task 1: the LLM's dashboard query, its plan, and a correctness check.
-- Run from the repo root with
--   sqlite3 Module03/warehouse.db ".read Module03/task1.sql"
-- Predicted plan (written before running):
--   SCAN order_line (largest table, no index), then SEARCH orders / customer / product
--   by their INTEGER PRIMARY KEYs, then TEMP B-TREE for GROUP BY and for ORDER BY.
.mode column
.headers on
.timer on

.print == 1. RUN the LLM's query
SELECT c.city,
       COUNT(DISTINCT c.customer_id) AS customers,
       SUM(ol.qty * p.price)         AS revenue
FROM customer c
JOIN orders o      ON o.customer_id = c.customer_id
JOIN order_line ol ON ol.order_id   = o.order_id
JOIN product p     ON p.product_id  = ol.product_id
WHERE strftime('%Y', o.ordered_on) = '2025'
GROUP BY c.city
ORDER BY revenue DESC;

.timer off
.print
.print == 2. PLAN of the LLM's query
EXPLAIN QUERY PLAN
SELECT c.city, COUNT(DISTINCT c.customer_id) AS customers, SUM(ol.qty * p.price) AS revenue
FROM customer c
JOIN orders o      ON o.customer_id = c.customer_id
JOIN order_line ol ON ol.order_id   = o.order_id
JOIN product p     ON p.product_id  = ol.product_id
WHERE strftime('%Y', o.ordered_on) = '2025'
GROUP BY c.city ORDER BY revenue DESC;

.print
.print == 3. PLAN of the workbook reference query (date range instead of strftime)
EXPLAIN QUERY PLAN
SELECT c.city, COUNT(DISTINCT c.customer_id) AS customers,
       SUM(ol.qty * p.price) AS revenue
FROM customer c
JOIN orders o     ON o.customer_id = c.customer_id
JOIN order_line ol ON ol.order_id = o.order_id
JOIN product p    ON p.product_id = ol.product_id
WHERE o.ordered_on >= '2025-01-01' AND o.ordered_on < '2026-01-01'
GROUP BY c.city
ORDER BY revenue DESC;

.print
.print == 4. CORRECTNESS: rows that differ between LLM and reference (empty = same answer)
WITH llm AS (
  SELECT c.city, COUNT(DISTINCT c.customer_id) AS customers, ROUND(SUM(ol.qty * p.price), 2) AS revenue
  FROM customer c JOIN orders o ON o.customer_id = c.customer_id
  JOIN order_line ol ON ol.order_id = o.order_id JOIN product p ON p.product_id = ol.product_id
  WHERE strftime('%Y', o.ordered_on) = '2025' GROUP BY c.city
), ref AS (
  SELECT c.city, COUNT(DISTINCT c.customer_id) AS customers, ROUND(SUM(ol.qty * p.price), 2) AS revenue
  FROM customer c JOIN orders o ON o.customer_id = c.customer_id
  JOIN order_line ol ON ol.order_id = o.order_id JOIN product p ON p.product_id = ol.product_id
  WHERE o.ordered_on >= '2025-01-01' AND o.ordered_on < '2026-01-01' GROUP BY c.city
)
SELECT 'only in llm' AS side, * FROM (SELECT * FROM llm EXCEPT SELECT * FROM ref)
UNION ALL
SELECT 'only in ref', * FROM (SELECT * FROM ref EXCEPT SELECT * FROM llm);

.print
.print == 5. EDGE CASES
.print -- why DISTINCT matters: customer rows counted without it
SELECT c.city, COUNT(c.customer_id) AS without_distinct, COUNT(DISTINCT c.customer_id) AS with_distinct
FROM customer c JOIN orders o ON o.customer_id = c.customer_id
JOIN order_line ol ON ol.order_id = o.order_id
WHERE o.ordered_on >= '2025-01-01' AND o.ordered_on < '2026-01-01'
GROUP BY c.city;
.print -- customers with no 2025 orders (an inner join silently drops them)
SELECT COUNT(*) AS customers_without_2025_orders FROM customer c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id
                  AND o.ordered_on >= '2025-01-01' AND o.ordered_on < '2026-01-01');
