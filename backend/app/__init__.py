from __future__ import annotations

from pathlib import Path

import click
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import Config
from .extensions import db, login_manager
from .models import User
from .seed import seed_database


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object or Config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "未设置 SECRET_KEY。请在 .env 文件中配置 SECRET_KEY=xxx 或设置系统环境变量。"
        )
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError(
            "未设置 DATABASE_URL。请在 .env 文件中配置数据库连接串或设置系统环境变量。"
        )
    default_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    app.config["FRONTEND_DIST"] = Path(
        app.config.get("FRONTEND_DIST", default_frontend_dist)
    )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = None
    CORS(
        app,
        supports_credentials=True,
        resources={
            r"/api/*": {
                "origins": app.config["CORS_ORIGINS"],
                "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    from .routes.admin import bp as admin_bp
    from .routes.auth import bp as auth_bp
    from .routes.orders import bp as orders_bp
    from .routes.tickets import bp as tickets_bp
    from .routes.trips import bp as trips_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(admin_bp)

    @app.after_request
    def apply_production_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )

        if request.path.startswith("/api/"):
            response.cache_control.no_store = True
        elif request.path.startswith("/assets/") and response.status_code == 200:
            response.cache_control.no_cache = None
            response.cache_control.public = True
            response.cache_control.max_age = 31_536_000
            response.cache_control.immutable = True
        elif response.mimetype == "text/html":
            response.cache_control.no_cache = True

        return response

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return api_error("AUTH_REQUIRED", "请先登录。", 401)

    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError):
        return api_error("VALIDATION_ERROR", str(error), 422)

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error: SQLAlchemyError):
        db.session.rollback()
        app.logger.exception("Database error: %s", error)
        return api_error("DATABASE_ERROR", "数据库操作失败，请检查数据或稍后重试。", 500)

    @app.errorhandler(404)
    def handle_not_found(_error):
        return api_error("NOT_FOUND", "请求的资源不存在。", 404)

    @app.get("/healthz")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/readyz")
    def readiness():
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.warning("Database readiness check failed")
            return jsonify({"status": "unavailable"}), 503
        return jsonify({"status": "ready"})

    @app.get("/")
    def index():
        frontend_dist = app.config["FRONTEND_DIST"]
        if frontend_dist.exists():
            return send_from_directory(frontend_dist, "index.html")
        return jsonify({"status": "ok"})

    @app.get("/<path:path>")
    def static_proxy(path: str):
        if path.startswith("api/"):
            return api_error("NOT_FOUND", "请求的接口不存在。", 404)
        frontend_dist = app.config["FRONTEND_DIST"]
        if frontend_dist.exists() and (frontend_dist / path).exists():
            return send_from_directory(frontend_dist, path)
        if frontend_dist.exists():
            return send_from_directory(frontend_dist, "index.html")
        return api_error("NOT_FOUND", "请求的资源不存在。", 404)

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        print("Database tables initialized.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        db.create_all()
        seed_database()
        print("Demo data initialized.")

    @app.cli.command("create-admin")
    @click.option("--username", required=True)
    @click.option("--display-name", required=True)
    @click.option("--phone")
    @click.option(
        "--password",
        envvar="ADMIN_PASSWORD",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
    )
    def create_admin_command(
        username: str,
        display_name: str,
        phone: str | None,
        password: str,
    ):
        username = username.strip()
        display_name = display_name.strip()
        phone = phone.strip() if phone else None
        if not 2 <= len(username) <= 64:
            raise click.ClickException("Username must be between 2 and 64 characters.")
        if not display_name:
            raise click.ClickException("Display name is required.")
        if len(password) < 12:
            raise click.ClickException("Admin password must contain at least 12 characters.")
        if User.query.filter_by(username=username).first():
            raise click.ClickException("Username already exists.")
        if phone and User.query.filter_by(phone=phone).first():
            raise click.ClickException("Phone number already exists.")

        admin = User(
            username=username,
            role="ADMIN",
            display_name=display_name,
            phone=phone,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin account '{username}' created.")

    return app


def api_error(code: str, message: str, status: int, details: object | None = None):
    payload: dict[str, object] = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return jsonify(payload), status
