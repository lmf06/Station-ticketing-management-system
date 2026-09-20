from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from flask import Blueprint, request
from flask_login import current_user
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import FareRule, Order, Route, Seat, Station, Ticket, TicketOperation, Trip, User, Vehicle
from ..services import sales_stats, serialize_ticket, serialize_trip, serialize_trips
from .common import error, json_body, ok, required, roles_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/users")
@roles_required("ADMIN")
def users():
    rows = User.query.order_by(User.role, User.username).all()
    return ok({"data": [user.to_dict() for user in rows]})


@bp.patch("/users/<int:user_id>")
@roles_required("ADMIN")
def update_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return error("NOT_FOUND", "用户不存在。", 404)
    data = json_body()
    if "username" in data:
        new_username = data["username"].strip()
        if len(new_username) < 2 or len(new_username) > 64:
            return error("VALIDATION_ERROR", "用户名长度应在 2-64 位之间。", 422)
        if User.query.filter(User.username == new_username, User.id != user_id).first():
            return error("USERNAME_EXISTS", "用户名已存在。", 409)
        user.username = new_username
    if "displayName" in data:
        user.display_name = data["displayName"].strip()
    if "phone" in data:
        new_phone = data["phone"].strip()
        if User.query.filter(User.phone == new_phone, User.id != user_id).first():
            return error("PHONE_EXISTS", "该手机号已被其他用户使用。", 409)
        user.phone = new_phone
    if "isActive" in data:
        user.is_active_flag = bool(data["isActive"])
    if "role" in data and data["role"] in {"PASSENGER", "STAFF", "ADMIN"}:
        user.role = data["role"]
    db.session.commit()
    return ok({"user": user.to_dict()})


@bp.delete("/users/<int:user_id>")
@roles_required("ADMIN")
def delete_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return error("NOT_FOUND", "用户不存在。", 404)
    if user.id == current_user.id:
        return error("CANNOT_DELETE_SELF", "不能删除自己的账号。", 422)
    if user.role == "ADMIN" and User.query.filter_by(role="ADMIN", is_active_flag=True).count() <= 1:
        return error("LAST_ADMIN", "不能删除最后一个管理员账号。", 422)

    to_delete = []

    if user.passenger_profile:
        to_delete.append(user.passenger_profile)

    order_ids = [row[0] for row in db.session.query(Order.id).filter_by(user_id=user.id).all()]
    if order_ids:
        ticket_ids = [row[0] for row in db.session.query(Ticket.id).filter(Ticket.order_id.in_(order_ids)).all()]
        if ticket_ids:
            ops = TicketOperation.query.filter(TicketOperation.ticket_id.in_(ticket_ids)).all()
            to_delete.extend(ops)
            to_delete.extend(Ticket.query.filter(Ticket.id.in_(ticket_ids)).all())
        to_delete.extend(Order.query.filter(Order.id.in_(order_ids)).all())

    ops = TicketOperation.query.filter_by(operator_user_id=user.id).all()
    to_delete.extend(ops)
    to_delete.append(user)

    for obj in to_delete:
        db.session.delete(obj)

    db.session.commit()
    return ok({"message": "用户已删除。"})


@bp.get("/stations")
@roles_required("ADMIN", "STAFF")
def admin_stations():
    rows = Station.query.order_by(Station.city, Station.name).all()
    return ok({"data": [row.to_dict() for row in rows]})


@bp.post("/stations")
@roles_required("ADMIN")
def create_station():
    data = json_body()
    required(data, "name", "city", "address")
    station = Station(name=data["name"].strip(), city=data["city"].strip(), address=data["address"].strip(), is_active=bool(data.get("isActive", True)))
    db.session.add(station)
    db.session.commit()
    return ok({"station": station.to_dict()}, 201)


@bp.patch("/stations/<int:station_id>")
@roles_required("ADMIN")
def update_station(station_id: int):
    station = db.session.get(Station, station_id)
    if not station:
        return error("NOT_FOUND", "站点不存在。", 404)
    data = json_body()
    for source, attr in [("name", "name"), ("city", "city"), ("address", "address")]:
        if source in data:
            setattr(station, attr, data[source].strip())
    if "isActive" in data:
        station.is_active = bool(data["isActive"])
    db.session.commit()
    return ok({"station": station.to_dict()})


@bp.get("/routes")
@roles_required("ADMIN", "STAFF")
def routes():
    rows = Route.query.order_by(Route.code).all()
    return ok({"data": [row.to_dict() for row in rows]})


@bp.post("/routes")
@roles_required("ADMIN")
def create_route():
    data = json_body()
    required(data, "code", "name", "originStationId", "destinationStationId", "distanceKm")
    route = Route(
        code=data["code"].strip(),
        name=data["name"].strip(),
        origin_station_id=int(data["originStationId"]),
        destination_station_id=int(data["destinationStationId"]),
        distance_km=Decimal(str(data["distanceKm"])),
        is_active=bool(data.get("isActive", True)),
    )
    db.session.add(route)
    db.session.commit()
    return ok({"route": route.to_dict()}, 201)


@bp.get("/vehicles")
@roles_required("ADMIN", "STAFF")
def vehicles():
    rows = Vehicle.query.order_by(Vehicle.plate_number).all()
    return ok({"data": [row.to_dict() for row in rows]})


@bp.post("/vehicles")
@roles_required("ADMIN")
def create_vehicle():
    data = json_body()
    required(data, "plateNumber", "model", "seatCount")
    vehicle = Vehicle(plate_number=data["plateNumber"].strip(), model=data["model"].strip(), seat_count=int(data["seatCount"]), status=data.get("status", "ACTIVE"))
    db.session.add(vehicle)
    db.session.flush()
    for number in range(1, vehicle.seat_count + 1):
        db.session.add(Seat(vehicle_id=vehicle.id, seat_number=str(number), seat_type="STANDARD"))
    db.session.commit()
    return ok({"vehicle": vehicle.to_dict()}, 201)


@bp.get("/trips")
@roles_required("ADMIN", "STAFF")
def admin_trips():
    rows = (
        Trip.query.options(
            joinedload(Trip.route).joinedload(Route.origin_station),
            joinedload(Trip.route).joinedload(Route.destination_station),
            joinedload(Trip.vehicle),
        )
        .order_by(Trip.departure_time.desc())
        .all()
    )
    return ok({"data": serialize_trips(rows)})


@bp.post("/trips")
@roles_required("ADMIN")
def create_trip():
    data = json_body()
    required(data, "routeId", "vehicleId", "departureTime", "arrivalTime", "baseFare")
    trip = Trip(
        route_id=int(data["routeId"]),
        vehicle_id=int(data["vehicleId"]),
        departure_time=datetime.fromisoformat(data["departureTime"]),
        arrival_time=datetime.fromisoformat(data["arrivalTime"]),
        base_fare=Decimal(str(data["baseFare"])),
        status=data.get("status", "OPEN"),
    )
    db.session.add(trip)
    db.session.commit()
    return ok({"trip": serialize_trip(trip)}, 201)


@bp.get("/fare-rules")
@roles_required("ADMIN", "STAFF")
def fare_rules():
    rows = FareRule.query.order_by(FareRule.priority.desc(), FareRule.start_date.desc()).all()
    return ok({"data": [row.to_dict() for row in rows]})


@bp.post("/fare-rules")
@roles_required("ADMIN")
def create_fare_rule():
    data = json_body()
    required(data, "name", "startDate", "endDate", "multiplier")
    rule = FareRule(
        name=data["name"].strip(),
        start_date=datetime.strptime(data["startDate"], "%Y-%m-%d").date(),
        end_date=datetime.strptime(data["endDate"], "%Y-%m-%d").date(),
        multiplier=Decimal(str(data["multiplier"])),
        priority=int(data.get("priority", 0)),
        is_active=bool(data.get("isActive", True)),
    )
    db.session.add(rule)
    db.session.commit()
    return ok({"fareRule": rule.to_dict()}, 201)


@bp.get("/stats")
@roles_required("ADMIN", "STAFF")
def stats():
    return ok({"data": sales_stats()})


@bp.get("/orders")
@roles_required("ADMIN", "STAFF")
def orders():
    status = request.args.get("status")
    query = Ticket.query
    if status:
        query = query.filter(Ticket.status == status)
    rows = query.order_by(Ticket.created_at.desc()).all()
    return ok({"data": [serialize_ticket(row) for row in rows]})
