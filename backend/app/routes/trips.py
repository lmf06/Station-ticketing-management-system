from __future__ import annotations

from datetime import datetime, time

from flask import Blueprint, request

from ..models import Route, Station, Trip
from ..services import serialize_trip
from .common import ok

bp = Blueprint("trips", __name__, url_prefix="/api")


@bp.get("/stations")
def list_stations():
    stations = Station.query.filter_by(is_active=True).order_by(Station.city, Station.name).all()
    return ok({"data": [station.to_dict() for station in stations]})


@bp.get("/trips")
def list_trips():
    query = Trip.query.join(Route).filter(Trip.status == "OPEN")
    from_station_id = request.args.get("fromStationId", type=int)
    to_station_id = request.args.get("toStationId", type=int)
    date_text = request.args.get("date")
    if from_station_id:
        query = query.filter(Route.origin_station_id == from_station_id)
    if to_station_id:
        query = query.filter(Route.destination_station_id == to_station_id)
    if date_text:
        day = datetime.strptime(date_text, "%Y-%m-%d").date()
        query = query.filter(Trip.departure_time >= datetime.combine(day, time.min), Trip.departure_time <= datetime.combine(day, time.max))
    else:
        query = query.filter(Trip.departure_time >= datetime.utcnow())
    trips = query.order_by(Trip.departure_time.asc()).all()
    return ok({"data": [serialize_trip(trip) for trip in trips]})
