from __future__ import annotations

from flask import Blueprint
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import PassengerProfile, User
from .common import error, json_body, ok, required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    data = json_body()
    required(data, "username", "password", "displayName", "idCard", "phone")
    username = data["username"].strip()
    password = data["password"].strip()
    if len(username) < 2 or len(username) > 64:
        return error("VALIDATION_ERROR", "用户名长度应在 2-64 位之间。", 422)
    if len(password) < 6:
        return error("VALIDATION_ERROR", "密码长度不能少于 6 位。", 422)
    if User.query.filter_by(username=username).first():
        return error("USERNAME_EXISTS", "用户名已存在。", 409)
    user = User(username=username, role="PASSENGER", display_name=data["displayName"].strip(), phone=data["phone"].strip())
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    db.session.add(PassengerProfile(user_id=user.id, real_name=user.display_name, id_card=data["idCard"].strip(), contact_phone=user.phone))
    db.session.commit()
    login_user(user)
    return ok({"user": user.to_dict()}, 201)


@bp.post("/login")
def login():
    data = json_body()
    required(data, "username", "password")
    user = User.query.filter_by(username=data["username"].strip()).first()
    if not user or not user.check_password(data["password"]):
        return error("INVALID_CREDENTIALS", "账号或密码错误。", 401)
    if not user.is_active:
        return error("USER_DISABLED", "账号已停用。", 403)
    login_user(user)
    return ok({"user": user.to_dict()})


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return ok({"message": "已退出登录。"})


@bp.get("/me")
def me():
    if not current_user.is_authenticated:
        return ok({"user": None})
    return ok({"user": current_user.to_dict()})
