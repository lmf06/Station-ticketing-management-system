from __future__ import annotations

from flask import Blueprint
from flask_login import current_user, login_required

from ..models import Order, Ticket
from ..services import TicketingError, exchange_ticket, refund_ticket, serialize_ticket
from .common import error, json_body, ok, required

bp = Blueprint("tickets", __name__, url_prefix="/api")


@bp.get("/my/tickets")
@login_required
def my_tickets():
    query = Ticket.query.join(Ticket.order)
    if current_user.role == "PASSENGER":
        query = query.filter(Order.user_id == current_user.id)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return ok({"data": [serialize_ticket(ticket) for ticket in tickets]})


@bp.post("/tickets/<int:ticket_id>/refund")
@login_required
def refund(ticket_id: int):
    try:
        ticket = refund_ticket(current_user, ticket_id)
    except TicketingError as exc:
        return error("TICKETING_ERROR", str(exc), 422)
    return ok({"ticket": serialize_ticket(ticket)})


@bp.post("/tickets/<int:ticket_id>/exchange")
@login_required
def exchange(ticket_id: int):
    data = json_body()
    required(data, "newTripId")
    try:
        ticket = exchange_ticket(current_user, ticket_id, int(data["newTripId"]))
    except TicketingError as exc:
        return error("TICKETING_ERROR", str(exc), 422)
    return ok({"ticket": serialize_ticket(ticket)}, 201)
