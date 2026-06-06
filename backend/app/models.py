from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="PASSENGER")
    display_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20))
    is_active_flag = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("role in ('PASSENGER','STAFF','ADMIN')", name="ck_users_role"),
        Index("ix_users_role", "role"),
    )

    @property
    def is_active(self) -> bool:
        return bool(self.is_active_flag)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "displayName": self.display_name,
            "phone": self.phone,
            "isActive": self.is_active,
        }


class PassengerProfile(TimestampMixin, db.Model):
    __tablename__ = "passenger_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    real_name = db.Column(db.String(80), nullable=False)
    id_card = db.Column(db.String(32), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)

    user = db.relationship("User", backref=db.backref("passenger_profile", uselist=False))


class Station(TimestampMixin, db.Model):
    __tablename__ = "stations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    city = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "city": self.city, "address": self.address, "isActive": self.is_active}


class Route(TimestampMixin, db.Model):
    __tablename__ = "routes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    origin_station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    destination_station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    distance_km = db.Column(db.Numeric(8, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    origin_station = db.relationship("Station", foreign_keys=[origin_station_id])
    destination_station = db.relationship("Station", foreign_keys=[destination_station_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "originStationId": self.origin_station_id,
            "destinationStationId": self.destination_station_id,
            "originStationName": self.origin_station.name if self.origin_station else None,
            "destinationStationName": self.destination_station.name if self.destination_station else None,
            "distanceKm": float(self.distance_km),
            "isActive": self.is_active,
        }


class RouteStop(TimestampMixin, db.Model):
    __tablename__ = "route_stops"

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    stop_order = db.Column(db.Integer, nullable=False)
    planned_offset_minutes = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("route_id", "stop_order", name="uq_route_stop_order"),)


class Vehicle(TimestampMixin, db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False, unique=True)
    model = db.Column(db.String(80), nullable=False)
    seat_count = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")

    __table_args__ = (
        CheckConstraint("seat_count > 0", name="ck_vehicle_seat_count"),
        CheckConstraint("status in ('ACTIVE','MAINTENANCE','RETIRED')", name="ck_vehicle_status"),
    )

    def to_dict(self) -> dict:
        return {"id": self.id, "plateNumber": self.plate_number, "model": self.model, "seatCount": self.seat_count, "status": self.status}


class Seat(TimestampMixin, db.Model):
    __tablename__ = "seats"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    seat_number = db.Column(db.String(12), nullable=False)
    seat_type = db.Column(db.String(20), nullable=False, default="STANDARD")

    vehicle = db.relationship("Vehicle", backref="seats")

    __table_args__ = (UniqueConstraint("vehicle_id", "seat_number", name="uq_vehicle_seat_number"),)


class Trip(TimestampMixin, db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    base_fare = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="OPEN")

    route = db.relationship("Route", backref="trips")
    vehicle = db.relationship("Vehicle")

    __table_args__ = (
        CheckConstraint("status in ('OPEN','CLOSED','CANCELLED')", name="ck_trip_status"),
        Index("ix_trips_departure_time", "departure_time"),
        Index("ix_trips_route_departure", "route_id", "departure_time"),
    )


class FareRule(TimestampMixin, db.Model):
    __tablename__ = "fare_rules"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    multiplier = db.Column(db.Numeric(5, 2), nullable=False, default=Decimal("1.00"))
    priority = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("multiplier > 0", name="ck_fare_rule_multiplier"),
        Index("ix_fare_rules_date_range", "start_date", "end_date", "priority"),
    )

    def applies_to(self, day: date) -> bool:
        return self.is_active and self.start_date <= day <= self.end_date

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "startDate": self.start_date.isoformat(),
            "endDate": self.end_date.isoformat(),
            "multiplier": float(self.multiplier),
            "priority": self.priority,
            "isActive": self.is_active,
        }


class Order(TimestampMixin, db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(32), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PAID")
    paid_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User")

    __table_args__ = (
        CheckConstraint("status in ('PAID','REFUNDED','PARTIAL_REFUND')", name="ck_order_status"),
        Index("ix_orders_user_status", "user_id", "status"),
    )


class Ticket(TimestampMixin, db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    ticket_no = db.Column(db.String(32), nullable=False, unique=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False)
    passenger_name = db.Column(db.String(80), nullable=False)
    passenger_id_card = db.Column(db.String(32), nullable=False)
    seat_number = db.Column(db.String(12), nullable=False)
    fare = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")

    order = db.relationship("Order", backref="tickets")
    trip = db.relationship("Trip", backref="tickets")

    __table_args__ = (
        CheckConstraint("status in ('ACTIVE','REFUNDED','EXCHANGED')", name="ck_ticket_status"),
        Index("ix_tickets_trip_status", "trip_id", "status"),
        Index("ix_tickets_order", "order_id"),
    )


class TicketOperation(TimestampMixin, db.Model):
    __tablename__ = "ticket_operations"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    operator_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    operation_type = db.Column(db.String(20), nullable=False)
    amount_delta = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    note = db.Column(db.String(255))

    ticket = db.relationship("Ticket")
    operator = db.relationship("User")

    __table_args__ = (
        CheckConstraint("operation_type in ('PURCHASE','REFUND','EXCHANGE_OUT','EXCHANGE_IN')", name="ck_ticket_operation_type"),
        Index("ix_ticket_operations_ticket", "ticket_id"),
    )
