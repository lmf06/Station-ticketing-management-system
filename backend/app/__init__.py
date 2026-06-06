from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

from .config import Config
from .extensions import db, login_manager
from .models import User
from .seed import seed_database


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object or Config)
    app.config["FRONTEND_DIST"] = Path(__file__).resolve().parents[2] / "frontend" / "dist"

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = None
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

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
        seed_database()
        print("Database initialized with sample data.")

    return app


def api_error(code: str, message: str, status: int, details: object | None = None):
    payload: dict[str, object] = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return jsonify(payload), status
