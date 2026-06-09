USE station_ticketing;

-- 1. 查询可售班次、余票和节假日浮动后票价
SELECT
  t.id AS trip_id,
  r.name AS route_name,
  s1.name AS origin_station,
  s2.name AS destination_station,
  t.departure_time,
  t.arrival_time,
  t.base_fare,
  ROUND(t.base_fare * COALESCE(fr.multiplier, 1.00), 2) AS sale_fare,
  v.seat_count - COUNT(CASE WHEN tk.status = 'ACTIVE' THEN 1 END) AS remaining_seats
FROM trips t
JOIN routes r ON r.id = t.route_id
JOIN stations s1 ON s1.id = r.origin_station_id
JOIN stations s2 ON s2.id = r.destination_station_id
JOIN vehicles v ON v.id = t.vehicle_id
LEFT JOIN fare_rules fr
  ON fr.is_active = TRUE
 AND DATE(t.departure_time) BETWEEN fr.start_date AND fr.end_date
LEFT JOIN tickets tk ON tk.trip_id = t.id
WHERE t.status = 'OPEN'
GROUP BY t.id, r.name, s1.name, s2.name, t.departure_time, t.arrival_time, t.base_fare, fr.multiplier, v.seat_count;

-- 2. 预售票事务核心逻辑示例：先锁定班次，再检查有效车票数，最后写入订单和车票。
START TRANSACTION;
SELECT * FROM trips WHERE id = 1 AND status = 'OPEN' FOR UPDATE;
SELECT COUNT(*) AS active_ticket_count FROM tickets WHERE trip_id = 1 AND status = 'ACTIVE';
-- 应用程序确认未超过 vehicles.seat_count 后执行 INSERT orders / tickets / ticket_operations。
COMMIT;

-- 3. 退票事务核心逻辑示例
START TRANSACTION;
SELECT * FROM tickets WHERE id = 1 FOR UPDATE;
UPDATE tickets SET status = 'REFUNDED' WHERE id = 1 AND status = 'ACTIVE';
INSERT INTO ticket_operations (ticket_id, operator_user_id, operation_type, amount_delta, note)
VALUES (1, 1, 'REFUND', -68.00, '退票释放座位');
COMMIT;

-- 4. 销售统计
SELECT
  COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) AS active_ticket_count,
  COUNT(CASE WHEN status = 'REFUNDED' THEN 1 END) AS refunded_ticket_count,
  COUNT(CASE WHEN status = 'EXCHANGED' THEN 1 END) AS exchanged_ticket_count,
  COALESCE(SUM(CASE WHEN status = 'ACTIVE' THEN fare ELSE 0 END), 0) AS active_sales_amount
FROM tickets;
