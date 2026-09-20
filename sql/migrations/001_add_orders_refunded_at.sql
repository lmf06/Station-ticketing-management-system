-- Run once for databases created before orders.refunded_at was added to mysql_schema.sql.
ALTER TABLE orders
  ADD COLUMN refunded_at DATETIME NULL AFTER paid_at;
