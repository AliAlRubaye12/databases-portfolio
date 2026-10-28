-- Task B proof: the m:n sketch (work orders <-> parts) as real tables.
-- Run from the repo root with
--   sqlite3 ":memory:" ".read Module02/cardinality-proof.sql"
PRAGMA foreign_keys = ON;
.mode column
.headers on

CREATE TABLE work_order (
    order_id   INTEGER PRIMARY KEY,
    opened_on  TEXT NOT NULL
);
CREATE TABLE part (
    part_no     TEXT PRIMARY KEY,
    description TEXT NOT NULL
);
-- the junction table: its key is the pair, so an order lists a part only once
CREATE TABLE work_order_part (
    order_id INTEGER NOT NULL REFERENCES work_order(order_id),
    part_no  TEXT    NOT NULL REFERENCES part(part_no),
    PRIMARY KEY (order_id, part_no)
);

INSERT INTO work_order VALUES (1, '2026-01-08'), (2, '2026-02-14');
INSERT INTO part VALUES ('P-1001', 'Ball bearing 6203'), ('P-1002', 'Spindle belt');
INSERT INTO work_order_part VALUES (1, 'P-1001'), (1, 'P-1002'), (2, 'P-1001');

.print == parts per order (an order has many parts)
SELECT order_id, COUNT(*) AS parts FROM work_order_part GROUP BY order_id;

.print
.print == orders per part (a part is in many orders)
SELECT part_no, COUNT(*) AS orders FROM work_order_part GROUP BY part_no;

.print
.print == max on both sides > 1  =>  m:n
SELECT (SELECT MAX(c) FROM (SELECT COUNT(*) c FROM work_order_part GROUP BY order_id)) AS max_parts_per_order,
       (SELECT MAX(c) FROM (SELECT COUNT(*) c FROM work_order_part GROUP BY part_no))  AS max_orders_per_part;

.print
.print == the key enforces "a part only once per order" - this insert must fail:
INSERT INTO work_order_part VALUES (1, 'P-1001');

.print
.print == and the foreign key rejects a part that does not exist - this insert must fail:
INSERT INTO work_order_part VALUES (2, 'P-9999');
