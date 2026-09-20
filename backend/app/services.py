from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from sqlalchemy import func

from .extensions import db
from .models import FareRule, Order, Seat, Ticket, TicketOperation, Trip, User


class TicketingError(ValueError):
    pass


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_trip_fare(trip: Trip) -> Decimal:
    day = trip.departure_time.date()
    rule = (
        FareRule.query.filter(
            FareRule.is_active.is_(True),
            FareRule.start_date <= day,
            FareRule.end_date >= day,
        )
        .order_by(FareRule.priority.desc(), FareRule.id.desc())
        .first()
    )
    return _calculate_trip_fare_with_rules(trip, [rule] if rule else [])


def _calculate_trip_fare_with_rules(trip: Trip, rules: list[FareRule]) -> Decimal:
    day = trip.departure_time.date()
    rule = next((candidate for candidate in rules if candidate.applies_to(day)), None)
    multiplier = Decimal(rule.multiplier) if rule else Decimal("1.00")
    return money(Decimal(trip.base_fare) * multiplier)


def remaining_seats(trip: Trip) -> int:
    sold = Ticket.query.filter_by(trip_id=trip.id, status="ACTIVE").count()
    return _remaining_seats_from_count(trip, sold)


def _remaining_seats_from_count(trip: Trip, sold: int) -> int:
    if trip.departure_time <= datetime.now(timezone.utc).replace(tzinfo=None):
        return 0
    return max(int(trip.vehicle.seat_count) - sold, 0)


def serialize_trip(
    trip: Trip,
    *,
    fare: Decimal | None = None,
    active_ticket_count: int | None = None,
) -> dict:
    route = trip.route
    resolved_fare = calculate_trip_fare(trip) if fare is None else fare
    resolved_remaining_seats = (
        remaining_seats(trip)
        if active_ticket_count is None
        else _remaining_seats_from_count(trip, active_ticket_count)
    )
    return {
        "id": trip.id,
        "routeId": trip.route_id,
        "routeCode": route.code,
        "routeName": route.name,
        "originStationId": route.origin_station_id,
        "originStationName": route.origin_station.name,
        "destinationStationId": route.destination_station_id,
        "destinationStationName": route.destination_station.name,
        "vehicleId": trip.vehicle_id,
        "plateNumber": trip.vehicle.plate_number,
        "departureTime": trip.departure_time.isoformat(),
        "arrivalTime": trip.arrival_time.isoformat(),
        "baseFare": float(trip.base_fare),
        "fare": float(resolved_fare),
        "remainingSeats": resolved_remaining_seats,
        "status": trip.status,
    }


def serialize_trips(trips: list[Trip]) -> list[dict]:
    if not trips:
        return []

    trip_ids = [trip.id for trip in trips]
    active_ticket_counts = dict(
        db.session.query(Ticket.trip_id, func.count(Ticket.id))
        .filter(Ticket.trip_id.in_(trip_ids), Ticket.status == "ACTIVE")
        .group_by(Ticket.trip_id)
        .all()
    )
    departure_days = [trip.departure_time.date() for trip in trips]
    fare_rules = (
        FareRule.query.filter(
            FareRule.is_active.is_(True),
            FareRule.start_date <= max(departure_days),
            FareRule.end_date >= min(departure_days),
        )
        .order_by(FareRule.priority.desc(), FareRule.id.desc())
        .all()
    )

    return [
        serialize_trip(
            trip,
            fare=_calculate_trip_fare_with_rules(trip, fare_rules),
            active_ticket_count=int(active_ticket_counts.get(trip.id, 0)),
        )
        for trip in trips
    ]


def serialize_ticket(ticket: Ticket) -> dict:
    trip = ticket.trip
    route = trip.route
    return {
        "id": ticket.id,
        "ticketNo": ticket.ticket_no,
        "orderNo": ticket.order.order_no,
        "tripId": ticket.trip_id,
        "routeName": route.name,
        "originStationName": route.origin_station.name,
        "destinationStationName": route.destination_station.name,
        "departureTime": trip.departure_time.isoformat(),
        "arrivalTime": trip.arrival_time.isoformat(),
        "passengerName": ticket.passenger_name,
        "passengerIdCard": ticket.passenger_id_card,
        "seatNumber": ticket.seat_number,
        "fare": float(ticket.fare),
        "status": ticket.status,
    }


def purchase_ticket(user: User, trip_id: int, passenger_name: str, passenger_id_card: str) -> Ticket:
    trip = _lock_trip(trip_id)
    _ensure_trip_open(trip)

    existing = (
        Ticket.query.join(Trip)
        .filter(
            Ticket.passenger_id_card == passenger_id_card.strip(),
            Ticket.trip_id == trip_id,
            Ticket.status == "ACTIVE",
        )
        .first()
    )
    if existing:
        raise TicketingError("该乘客已购买过本班次车票，请勿重复提交。")

    seat_number = _allocate_seat(trip)
    fare = calculate_trip_fare(trip)
    order = Order(order_no=_build_no("ORD"), user_id=user.id, total_amount=fare, status="PAID")
    db.session.add(order)
    db.session.flush()
    ticket = Ticket(
        ticket_no=_build_no("TKT"),
        order_id=order.id,
        trip_id=trip.id,
        passenger_name=passenger_name.strip(),
        passenger_id_card=passenger_id_card.strip(),
        seat_number=seat_number,
        fare=fare,
        status="ACTIVE",
    )
    db.session.add(ticket)
    db.session.flush()
    db.session.add(
        TicketOperation(
            ticket_id=ticket.id,
            operator_user_id=user.id,
            operation_type="PURCHASE",
            amount_delta=fare,
            note="预售购票",
        )
    )
    db.session.commit()
    return ticket


def refund_ticket(operator: User, ticket_id: int) -> Ticket:
    ticket = _lock_ticket(ticket_id)
    _ensure_ticket_access(operator, ticket)
    if ticket.status != "ACTIVE":
        raise TicketingError("只有有效车票可以退票。")
    ticket.status = "REFUNDED"
    order = ticket.order
    active_count = Ticket.query.filter_by(order_id=order.id, status="ACTIVE").count()
    order.status = "REFUNDED" if active_count == 0 else "PARTIAL_REFUND"
    order.refunded_at = datetime.now(timezone.utc)
    db.session.add(
        TicketOperation(
            ticket_id=ticket.id,
            operator_user_id=operator.id,
            operation_type="REFUND",
            amount_delta=-money(ticket.fare),
            note="退票释放座位",
        )
    )
    db.session.commit()
    return ticket


def exchange_ticket(operator: User, ticket_id: int, new_trip_id: int) -> Ticket:
    old_ticket = _lock_ticket(ticket_id)
    _ensure_ticket_access(operator, old_ticket)
    if old_ticket.status != "ACTIVE":
        raise TicketingError("只有有效车票可以换票。")
    new_trip = _lock_trip(new_trip_id)
    _ensure_trip_open(new_trip)
    if old_ticket.trip_id == new_trip.id:
        raise TicketingError("新班次不能与原班次相同。")
    new_seat = _allocate_seat(new_trip)
    old_ticket.status = "EXCHANGED"
    new_fare = calculate_trip_fare(new_trip)
    fare_diff = new_fare - old_ticket.fare
    new_ticket = Ticket(
        ticket_no=_build_no("TKT"),
        order_id=old_ticket.order_id,
        trip_id=new_trip.id,
        passenger_name=old_ticket.passenger_name,
        passenger_id_card=old_ticket.passenger_id_card,
        seat_number=new_seat,
        fare=new_fare,
        status="ACTIVE",
    )
    order = old_ticket.order
    order.total_amount = money(order.total_amount + fare_diff)
    db.session.add(new_ticket)
    db.session.flush()
    db.session.add(
        TicketOperation(
            ticket_id=old_ticket.id,
            operator_user_id=operator.id,
            operation_type="EXCHANGE_OUT",
            amount_delta=-money(old_ticket.fare),
            note=f"换出至班次 {new_trip.id}",
        )
    )
    exchange_in_note = f"由车票 {old_ticket.ticket_no} 换入"
    if fare_diff > 0:
        exchange_in_note += f"，补收差价 {money(fare_diff)} 元"
    elif fare_diff < 0:
        exchange_in_note += f"，退还差价 {money(abs(fare_diff))} 元"
    db.session.add(
        TicketOperation(
            ticket_id=new_ticket.id,
            operator_user_id=operator.id,
            operation_type="EXCHANGE_IN",
            amount_delta=new_fare,
            note=exchange_in_note,
        )
    )
    db.session.commit()
    return new_ticket


def sales_stats() -> dict:
    active_sales = (
        db.session.query(func.coalesce(func.sum(Ticket.fare), 0))
        .filter(Ticket.status == "ACTIVE")
        .scalar()
    )
    refunded = Ticket.query.filter(Ticket.status == "REFUNDED").count()
    active = Ticket.query.filter(Ticket.status == "ACTIVE").count()
    exchanged = Ticket.query.filter(Ticket.status == "EXCHANGED").count()
    return {
        "activeTicketCount": active,
        "refundedTicketCount": refunded,
        "exchangedTicketCount": exchanged,
        "activeSalesAmount": float(money(active_sales)),
    }


def _lock_trip(trip_id: int) -> Trip:
    query = Trip.query.filter_by(id=trip_id)
    if _supports_for_update(Trip):
        query = query.with_for_update()
    trip = query.first()
    if not trip:
        raise TicketingError("班次不存在。")
    return trip


def _lock_ticket(ticket_id: int) -> Ticket:
    query = Ticket.query.filter_by(id=ticket_id)
    if _supports_for_update(Ticket):
        query = query.with_for_update()
    ticket = query.first()
    if not ticket:
        raise TicketingError("车票不存在。")
    return ticket


def _supports_for_update(model: type) -> bool:
    return db.session.get_bind(mapper=model).dialect.name == "mysql"


def _ensure_trip_open(trip: Trip) -> None:
    if trip.status != "OPEN":
        raise TicketingError("班次当前不可售票。")
    if trip.departure_time <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise TicketingError("已发车班次不可售票。")


def _allocate_seat(trip: Trip) -> str:
    taken = {
        row[0]
        for row in db.session.query(Ticket.seat_number)
        .filter(Ticket.trip_id == trip.id, Ticket.status == "ACTIVE")
        .all()
    }
    configured_seats = [seat.seat_number for seat in Seat.query.filter_by(vehicle_id=trip.vehicle_id).order_by(Seat.id).all()]
    seat_pool = configured_seats or [str(i) for i in range(1, trip.vehicle.seat_count + 1)]
    for seat_number in seat_pool:
        if seat_number not in taken:
            return seat_number
    raise TicketingError("该班次余票不足。")


def _ensure_ticket_access(user: User, ticket: Ticket) -> None:
    if user.role == "STAFF":
        return
    if ticket.order.user_id != user.id:
        raise TicketingError("不能操作他人的车票。")


def _build_no(prefix: str) -> str:
    return f"{prefix}{datetime.now(timezone.utc):%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}"
