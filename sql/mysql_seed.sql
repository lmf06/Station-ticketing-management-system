USE station_ticketing;

INSERT INTO users (username, password_hash, role, display_name, phone) VALUES
('admin', 'scrypt:32768:8:1$4QWmhvvNwUrDnMLV$13cd57470583a57440d6651ea366f479880f0fcaac3c2205a9a527f1d97eced3d47cd13c3cd3a9b39751595c559cfb65f6772fbec487811c89b773de959b19eb', 'ADMIN', '系统管理员', '13800000000'),
('staff', 'scrypt:32768:8:1$VQoxFHfoMOZRFoUM$fb51dcf31d4f6acea4eb9a16f43f3bed97e218290ed9165ed05b091ea5acaca5f8b33aed6324412d03107c268d9065524d2ab78445aecab1ecb0351706d3a18d', 'STAFF', '售票员', '13800000001'),
('passenger', 'scrypt:32768:8:1$jutZTupYsApj0o6Z$2d3b24e3cb9fe830953e8699cf725a1a10139eb6664428be2d381a8d16d509b838b2a5ffed80d79544ca414bfa932c5c318117a5634d7a7509ff8c011c63718d', 'PASSENGER', '张三', '13800000002');

INSERT INTO passenger_profiles (user_id, real_name, id_card, contact_phone)
SELECT id, '张三', '330100200001010011', '13800000002' FROM users WHERE username = 'passenger';

INSERT INTO stations (name, city, address) VALUES
('杭州汽车客运中心', '杭州', '杭州市上城区九堡街道德胜东路'),
('宁波汽车南站', '宁波', '宁波市海曙区甬江大道'),
('绍兴客运中心', '绍兴', '绍兴市越城区中兴大道'),
('上海长途客运总站', '上海', '上海市静安区中兴路');

INSERT INTO routes (code, name, origin_station_id, destination_station_id, distance_km) VALUES
('HZ-NB', '杭州至宁波快线', 1, 2, 156.00),
('HZ-SX', '杭州至绍兴城际线', 1, 3, 63.50),
('HZ-SH', '杭州至上海商务线', 1, 4, 178.00);

INSERT INTO route_stops (route_id, station_id, stop_order, planned_offset_minutes) VALUES
(1, 1, 1, 0), (1, 2, 2, 130),
(2, 1, 1, 0), (2, 3, 2, 55),
(3, 1, 1, 0), (3, 4, 2, 160);

INSERT INTO vehicles (plate_number, model, seat_count, status) VALUES
('浙A10001', '宇通 ZK6122', 6, 'ACTIVE'),
('浙A10002', '金龙 XMQ6127', 8, 'ACTIVE'),
('浙A10003', '比亚迪 C9', 6, 'ACTIVE');

INSERT INTO seats (vehicle_id, seat_number, seat_type)
SELECT v.id, CAST(n.n AS CHAR), 'STANDARD'
FROM vehicles v
JOIN (
  SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
  UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
) n ON n.n <= v.seat_count;

INSERT INTO trips (route_id, vehicle_id, departure_time, arrival_time, base_fare, status) VALUES
(1, 1, '2026-06-07 08:30:00', '2026-06-07 10:40:00', 68.00, 'OPEN'),
(1, 2, '2026-06-07 14:00:00', '2026-06-07 16:10:00', 68.00, 'OPEN'),
(2, 3, '2026-06-07 09:10:00', '2026-06-07 10:05:00', 32.00, 'OPEN'),
(3, 2, '2026-06-08 07:50:00', '2026-06-08 10:30:00', 92.00, 'OPEN'),
(1, 1, '2026-06-20 08:30:00', '2026-06-20 10:40:00', 68.00, 'OPEN');

INSERT INTO fare_rules (name, start_date, end_date, multiplier, priority, is_active) VALUES
('端午节假日浮动', '2026-06-19', '2026-06-22', 1.20, 10, TRUE),
('普通日优惠', '2026-06-01', '2026-06-18', 0.95, 1, TRUE);
