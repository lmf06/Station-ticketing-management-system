from __future__ import annotations

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.seed import seed_database


@pytest.fixture()
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_database()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_invalid_login_uses_standard_error_shape(client):
    response = client.post("/api/auth/login", json={"username": "missing", "password": "bad"})

    assert response.status_code == 401
    assert response.json == {"error": {"code": "INVALID_CREDENTIALS", "message": "账号或密码错误。"}}


def test_trip_search_returns_public_contract(client):
    response = client.get("/api/trips")

    assert response.status_code == 200
    trip = response.json["data"][0]
    assert {"id", "routeName", "originStationName", "destinationStationName", "fare", "remainingSeats", "departureTime"} <= set(trip)
