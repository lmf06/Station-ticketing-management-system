from __future__ import annotations

import runpy
from pathlib import Path

import pytest
from sqlalchemy.exc import OperationalError

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import User


@pytest.fixture()
def clean_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_mysql_database_url_uses_the_installed_pymysql_driver():
    from app.config import normalize_database_url

    assert (
        normalize_database_url("mysql://user:password@db.example/station")
        == "mysql+pymysql://user:password@db.example/station"
    )
    assert normalize_database_url("mysql+pymysql://user:password@db/station") == (
        "mysql+pymysql://user:password@db/station"
    )


def test_production_mysql_driver_supports_mysql_8_rsa_authentication():
    repository_root = Path(__file__).resolve().parents[2]
    requirements = (repository_root / "backend" / "requirements.txt").read_text(
        encoding="utf-8"
    )

    assert "PyMySQL[rsa]==1.1.1" in requirements.splitlines()


def test_liveness_does_not_require_database(clean_app):
    response = clean_app.test_client().get("/healthz")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_readiness_checks_database_connection(clean_app):
    response = clean_app.test_client().get("/readyz")

    assert response.status_code == 200
    assert response.json == {"status": "ready"}


def test_readiness_returns_service_unavailable_when_database_is_down(clean_app, monkeypatch):
    with clean_app.app_context():
        def fail_query(*_args, **_kwargs):
            raise OperationalError("SELECT 1", {}, Exception("database unavailable"))

        monkeypatch.setattr(db.session(), "execute", fail_query)
        response = clean_app.test_client().get("/readyz")

    assert response.status_code == 503
    assert response.json == {"status": "unavailable"}


def test_responses_include_baseline_security_headers(clean_app):
    response = clean_app.test_client().get("/healthz")
    api_response = clean_app.test_client().get("/api/not-found")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
    assert "no-store" in api_response.headers["Cache-Control"]


def test_session_cookie_has_safe_browser_defaults():
    assert TestConfig.SESSION_COOKIE_HTTPONLY is True
    assert TestConfig.SESSION_COOKIE_SAMESITE == "Lax"


def test_frontend_assets_are_cached_but_html_is_revalidated(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<main>station app</main>", encoding="utf-8")
    (tmp_path / "assets" / "app-abcdef.js").write_text("export default 1", encoding="utf-8")
    static_config = type(
        "StaticConfig",
        (TestConfig,),
        {"FRONTEND_DIST": tmp_path},
    )
    app = create_app(static_config)
    client = app.test_client()

    index_response = client.get("/passenger/orders")
    asset_response = client.get("/assets/app-abcdef.js")

    assert index_response.status_code == 200
    assert b"station app" in index_response.data
    assert "no-cache" in index_response.headers["Cache-Control"]
    assert asset_response.status_code == 200
    assert "public" in asset_response.headers["Cache-Control"]
    assert "max-age=31536000" in asset_response.headers["Cache-Control"]
    assert "immutable" in asset_response.headers["Cache-Control"]


def test_init_db_does_not_create_demo_accounts(clean_app):
    runner = clean_app.test_cli_runner()

    result = runner.invoke(args=["init-db"])

    assert result.exit_code == 0
    with clean_app.app_context():
        assert User.query.count() == 0


def test_demo_seed_requires_explicit_command(clean_app):
    runner = clean_app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0

    result = runner.invoke(args=["seed-demo"])

    assert result.exit_code == 0
    with clean_app.app_context():
        assert User.query.count() == 3


def test_create_admin_command_bootstraps_production_account(clean_app):
    runner = clean_app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0

    result = runner.invoke(
        args=[
            "create-admin",
            "--username",
            "production-admin",
            "--display-name",
            "生产管理员",
            "--phone",
            "13900000000",
            "--password",
            "a-strong-production-password",
        ]
    )

    assert result.exit_code == 0
    with clean_app.app_context():
        admin = User.query.filter_by(username="production-admin").one()
        assert admin.role == "ADMIN"
        assert admin.check_password("a-strong-production-password")


def test_gunicorn_config_reads_platform_environment(monkeypatch):
    repository_root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("PORT", "9123")
    monkeypatch.setenv("WEB_CONCURRENCY", "3")
    monkeypatch.setenv("WEB_THREADS", "2")

    config = runpy.run_path(repository_root / "backend" / "gunicorn.conf.py")

    assert config["bind"] == "0.0.0.0:9123"
    assert config["workers"] == 3
    assert config["threads"] == 2
    assert config["accesslog"] == "-"
    assert config["errorlog"] == "-"
