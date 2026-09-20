from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import event

from app import create_app
from app.config import Config, TestConfig
from app.extensions import db
from app.models import Trip
from app.seed import seed_database


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_database()
        yield app
        db.session.remove()
        db.drop_all()


def test_application_rejects_missing_database_url():
    class MissingDatabaseConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = None

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        create_app(MissingDatabaseConfig)


def test_database_connections_are_checked_before_checkout():
    assert Config.SQLALCHEMY_ENGINE_OPTIONS["pool_pre_ping"] is True


@pytest.mark.parametrize(
    ("dialect_name", "expected"),
    [("mysql", True), ("sqlite", False)],
)
def test_row_lock_support_uses_the_resolved_session_bind(app, monkeypatch, dialect_name, expected):
    from app.services import _supports_for_update

    with app.app_context():
        bind = SimpleNamespace(dialect=SimpleNamespace(name=dialect_name))
        monkeypatch.setattr(db.session(), "get_bind", lambda **_kwargs: bind)

        assert _supports_for_update(Trip) is expected


def test_mysql_schema_and_migration_include_order_refund_timestamp():
    repository_root = Path(__file__).resolve().parents[2]
    schema = (repository_root / "sql" / "mysql_schema.sql").read_text(encoding="utf-8")
    migration = (
        repository_root / "sql" / "migrations" / "001_add_orders_refunded_at.sql"
    ).read_text(encoding="utf-8")

    orders_definition = schema.split("CREATE TABLE orders (", 1)[1].split(") ENGINE=InnoDB", 1)[0]
    assert "refunded_at DATETIME NULL" in orders_definition
    assert "ADD COLUMN refunded_at DATETIME NULL" in migration


def test_public_trip_list_uses_a_bounded_number_of_queries(app):
    statements: list[str] = []

    with app.app_context():
        def record_statement(_conn, _cursor, statement, _parameters, _context, _executemany):
            statements.append(statement)

        event.listen(db.engine, "before_cursor_execute", record_statement)
        try:
            response = app.test_client().get("/api/trips")
        finally:
            event.remove(db.engine, "before_cursor_execute", record_statement)

    assert response.status_code == 200
    assert len(response.json["data"]) >= 4
    assert len(statements) <= 3
