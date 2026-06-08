from __future__ import annotations

from flask import Blueprint
from flask_login import current_user

from ..models import PassengerProfile
from ..services import TicketingError, purchase_ticket, serialize_ticket
from .common import error, json_body, ok, required, roles_required

bp = Blueprint("orders", __name__, url_prefix="/api")


@bp.post("/orders")
@roles_required("STAFF", "PASSENGER")
def create_order():
    data = json_body()
    required(data, "tripId")
    passenger_name = (data.get("passengerName") or "").strip()
    passenger_id_card = (data.get("passengerIdCard") or "").strip()
    if not passenger_name or not passenger_id_card:
        profile = PassengerProfile.query.filter_by(user_id=current_user.id).first()
        if profile:
            passenger_name = passenger_name or profile.real_name
            passenger_id_card = passenger_id_card or profile.id_card
    if not passenger_name or not passenger_id_card:
        return error("PASSENGER_REQUIRED", "请填写乘车人姓名和证件号。", 422)
    try:
        ticket = purchase_ticket(current_user, int(data["tripId"]), passenger_name, passenger_id_card)
    except TicketingError as exc:
        return error("TICKETING_ERROR", str(exc), 422)
    return ok({"ticket": serialize_ticket(ticket)}, 201)
