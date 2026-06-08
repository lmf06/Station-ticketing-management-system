from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from .extensions import db
from .models import FareRule, PassengerProfile, Route, RouteStop, Seat, Station, Trip, User, Vehicle


def seed_database() -> None:
    if User.query.count() > 0:
        return

    admin = User(username="admin", role="ADMIN", display_name="系统管理员", phone="13800000000")
    admin.set_password("admin123")
    staff = User(username="staff", role="STAFF", display_name="售票员", phone="13800000001")
    staff.set_password("staff123")
    passenger = User(username="passenger", role="PASSENGER", display_name="张三", phone="13800000002")
    passenger.set_password("passenger123")
    db.session.add_all([admin, staff, passenger])
    db.session.flush()
    db.session.add(PassengerProfile(user_id=passenger.id, real_name="张三", id_card="330100200001010011", contact_phone="13800000002"))

    hz = Station(name="杭州汽车客运中心", city="杭州", address="杭州市上城区九堡街道德胜东路")
    nb = Station(name="宁波汽车南站", city="宁波", address="宁波市海曙区甬江大道")
    sx = Station(name="绍兴客运中心", city="绍兴", address="绍兴市越城区中兴大道")
    sh = Station(name="上海长途客运总站", city="上海", address="上海市静安区中兴路")
    db.session.add_all([hz, nb, sx, sh])
    db.session.flush()

    routes = [
        Route(code="HZ-NB", name="杭州至宁波快线", origin_station_id=hz.id, destination_station_id=nb.id, distance_km=Decimal("156.00")),
        Route(code="HZ-SX", name="杭州至绍兴城际线", origin_station_id=hz.id, destination_station_id=sx.id, distance_km=Decimal("63.50")),
        Route(code="HZ-SH", name="杭州至上海商务线", origin_station_id=hz.id, destination_station_id=sh.id, distance_km=Decimal("178.00")),
    ]
    db.session.add_all(routes)
    db.session.flush()
    for route in routes:
        db.session.add(RouteStop(route_id=route.id, station_id=route.origin_station_id, stop_order=1, planned_offset_minutes=0))
        db.session.add(RouteStop(route_id=route.id, station_id=route.destination_station_id, stop_order=2, planned_offset_minutes=120))

    bus_a = Vehicle(plate_number="浙A10001", model="宇通 ZK6122", seat_count=6, status="ACTIVE")
    bus_b = Vehicle(plate_number="浙A10002", model="金龙 XMQ6127", seat_count=8, status="ACTIVE")
    bus_c = Vehicle(plate_number="浙A10003", model="比亚迪 C9", seat_count=6, status="ACTIVE")
    db.session.add_all([bus_a, bus_b, bus_c])
    db.session.flush()
    for vehicle in [bus_a, bus_b, bus_c]:
        for number in range(1, vehicle.seat_count + 1):
            db.session.add(Seat(vehicle_id=vehicle.id, seat_number=str(number), seat_type="STANDARD"))

    today = datetime.now(timezone.utc).date()
    db.session.add_all(
        [
            Trip(route_id=routes[0].id, vehicle_id=bus_a.id, departure_time=datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(hour=8, minute=30), arrival_time=datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(hour=10, minute=40), base_fare=Decimal("68.00")),
            Trip(route_id=routes[0].id, vehicle_id=bus_b.id, departure_time=datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(hour=14, minute=0), arrival_time=datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(hour=16, minute=10), base_fare=Decimal("68.00")),
            Trip(route_id=routes[1].id, vehicle_id=bus_c.id, departure_time=datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(hour=9, minute=10), arrival_time=datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(hour=10, minute=5), base_fare=Decimal("32.00")),
            Trip(route_id=routes[2].id, vehicle_id=bus_b.id, departure_time=datetime.combine(today + timedelta(days=2), datetime.min.time()).replace(hour=7, minute=50), arrival_time=datetime.combine(today + timedelta(days=2), datetime.min.time()).replace(hour=10, minute=30), base_fare=Decimal("92.00")),
            Trip(route_id=routes[0].id, vehicle_id=bus_a.id, departure_time=datetime(2026, 6, 20, 8, 30), arrival_time=datetime(2026, 6, 20, 10, 40), base_fare=Decimal("68.00")),
        ]
    )
    db.session.add(FareRule(name="端午节假日浮动", start_date=date(2026, 6, 19), end_date=date(2026, 6, 22), multiplier=Decimal("1.20"), priority=10))
    db.session.commit()
