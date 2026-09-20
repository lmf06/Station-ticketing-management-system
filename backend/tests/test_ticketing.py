from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import FareRule, Ticket, Trip, User
from app.seed import seed_database
from app.services import calculate_trip_fare, purchase_ticket, remaining_seats


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_database()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username="passenger", password="passenger123"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_holiday_fare_rule_uses_highest_priority(app):
    with app.app_context():
        trip = Trip.query.first()
        trip.departure_time = datetime(2026, 6, 20, 8, 0)
        db.session.add(FareRule(name="低优先级", start_date=trip.departure_time.date(), end_date=trip.departure_time.date(), multiplier=Decimal("1.10"), priority=1))
        db.session.add(FareRule(name="高优先级", start_date=trip.departure_time.date(), end_date=trip.departure_time.date(), multiplier=Decimal("1.50"), priority=99))
        db.session.commit()

        assert calculate_trip_fare(trip) == Decimal("102.00")


def test_purchase_ticket_allocates_seat_and_reduces_inventory(app):
    with app.app_context():
        user = User.query.filter_by(username="passenger").first()
        trip = Trip.query.first()
        trip.departure_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
        db.session.commit()
        before = remaining_seats(trip)

        ticket = purchase_ticket(user, trip.id, "张三", "330100200001010011")

        assert ticket.id is not None
        assert ticket.status == "ACTIVE"
        assert ticket.seat_number == "1"
        assert remaining_seats(trip) == before - 1


def test_purchase_rejects_oversell(app):
    with app.app_context():
        user = User.query.filter_by(username="passenger").first()
        trip = Trip.query.first()
        trip.departure_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
        db.session.commit()
        for index in range(trip.vehicle.seat_count):
            purchase_ticket(user, trip.id, f"乘客{index}", f"33010020000101{index:04d}")

        with pytest.raises(ValueError, match="余票不足"):
            purchase_ticket(user, trip.id, "超售乘客", "330100200001019999")


def test_api_refund_releases_seat(client, app):
    assert login(client).status_code == 200
    trip_id = client.get("/api/trips").json["data"][0]["id"]
    created = client.post("/api/orders", json={"tripId": trip_id}).json["ticket"]
    before_refund = client.get("/api/trips").json["data"][0]["remainingSeats"]

    response = client.post(f"/api/tickets/{created['id']}/refund")

    assert response.status_code == 200
    assert response.json["ticket"]["status"] == "REFUNDED"
    after_refund = client.get("/api/trips").json["data"][0]["remainingSeats"]
    assert after_refund == before_refund + 1


def test_api_exchange_creates_new_active_ticket_and_closes_old_one(client, app):
    assert login(client).status_code == 200
    trips = client.get("/api/trips").json["data"]
    original_trip_id = trips[0]["id"]
    new_trip_id = next(trip["id"] for trip in trips if trip["id"] != original_trip_id)
    old_ticket = client.post("/api/orders", json={"tripId": original_trip_id}).json["ticket"]

    response = client.post(f"/api/tickets/{old_ticket['id']}/exchange", json={"newTripId": new_trip_id})

    assert response.status_code == 201
    assert response.json["ticket"]["tripId"] == new_trip_id
    with app.app_context():
        assert db.session.get(Ticket, old_ticket["id"]).status == "EXCHANGED"


def test_admin_endpoints_require_admin_role(client):
    assert login(client, "passenger", "passenger123").status_code == 200
    forbidden = client.post("/api/admin/stations", json={"name": "测试站", "city": "杭州", "address": "测试地址"})
    assert forbidden.status_code == 403

    client.post("/api/auth/logout")
    assert login(client, "admin", "admin123").status_code == 200
    allowed = client.post("/api/admin/stations", json={"name": "测试站", "city": "杭州", "address": "测试地址"})
    assert allowed.status_code == 201


def test_staff_cannot_access_admin_only_endpoints(client):
    assert login(client, "staff", "staff123").status_code == 200
    response = client.post("/api/admin/stations", json={"name": "测试站", "city": "杭州", "address": "测试地址"})
    assert response.status_code == 403


def test_register_duplicate_username(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "passenger", "password": "test123", "displayName": "测试", "idCard": "330100200001010012", "phone": "13800000003"},
    )
    assert response.status_code == 409
    assert response.json["error"]["code"] == "USERNAME_EXISTS"


def test_register_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "12", "displayName": "测试", "idCard": "330100200001010012", "phone": "13800000003"},
    )
    assert response.status_code == 422


def test_disabled_user_cannot_login(client, app):
    with app.app_context():
        user = User.query.filter_by(username="passenger").first()
        user.is_active_flag = False
        db.session.commit()
    response = login(client, "passenger", "passenger123")
    assert response.status_code == 403
    with app.app_context():
        user = User.query.filter_by(username="passenger").first()
        user.is_active_flag = True
        db.session.commit()


def test_exchange_records_fare_diff(client, app):
    assert login(client, "passenger", "passenger123").status_code == 200
    trips = client.get("/api/trips").json["data"]
    cheaper_trip = next((t for t in trips if float(t["fare"]) < 40), trips[0])
    expensive_trip = next((t for t in trips if float(t["fare"]) > 60 and t["id"] != cheaper_trip["id"]), trips[0])
    ticket = client.post("/api/orders", json={"tripId": cheaper_trip["id"]}).json["ticket"]
    response = client.post(f"/api/tickets/{ticket['id']}/exchange", json={"newTripId": expensive_trip["id"]})
    assert response.status_code == 201

    with app.app_context():
        from app.models import TicketOperation
        ops = (
            TicketOperation.query
            .filter(TicketOperation.ticket_id == response.json["ticket"]["id"])
            .order_by(TicketOperation.id.desc())
            .first()
        )
        assert ops is not None
        assert "差价" in (ops.note or "")


def test_duplicate_passenger_blocked(client, app):
    assert login(client, "passenger", "passenger123").status_code == 200
    trips = client.get("/api/trips").json["data"]
    trip_id = trips[0]["id"]
    resp1 = client.post("/api/orders", json={"tripId": trip_id, "passengerName": "重复测试", "passengerIdCard": "330100200001019999"})
    assert resp1.status_code == 201
    resp2 = client.post("/api/orders", json={"tripId": trip_id, "passengerName": "重复测试", "passengerIdCard": "330100200001019999"})
    assert resp2.status_code == 422
    assert "重复" in resp2.json["error"]["message"]


def test_after_refund_seat_can_be_reassigned(client, app):
    assert login(client, "passenger", "passenger123").status_code == 200
    trips = client.get("/api/trips").json["data"]
    trip_id = trips[0]["id"]
    ticket1 = client.post("/api/orders", json={"tripId": trip_id, "passengerName": "乘客A", "passengerIdCard": "33010020000101A001"}).json["ticket"]
    seat1 = ticket1["seatNumber"]
    client.post(f"/api/tickets/{ticket1['id']}/refund")
    ticket2 = client.post("/api/orders", json={"tripId": trip_id, "passengerName": "乘客B", "passengerIdCard": "33010020000101B002"}).json["ticket"]
    assert ticket2["seatNumber"] == seat1
