from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import jsonify, request
from flask_login import current_user


def json_body() -> dict:
    return request.get_json(silent=True) or {}


def ok(data: object | None = None, status: int = 200):
    return jsonify(data if data is not None else {}), status


def error(code: str, message: str, status: int = 400, details: object | None = None):
    payload: dict[str, object] = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return jsonify(payload), status


def roles_required(*roles: str):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return error("AUTH_REQUIRED", "请先登录。", 401)
            if current_user.role not in roles:
                return error("FORBIDDEN", "当前账号没有权限执行此操作。", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def required(data: dict, *keys: str) -> None:
    missing = [key for key in keys if data.get(key) in (None, "")]
    if missing:
        raise ValueError(f"缺少必要字段：{', '.join(missing)}")
