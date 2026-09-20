from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]


def normalize_database_url(url: str | None) -> str | None:
    if url and url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+pymysql://", 1)
    return url


class Config:
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_ENGINE_OPTIONS = {
        "hide_parameters": True,
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "5")),
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_use_lifo": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")]
    JSON_AS_ASCII = False


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {"hide_parameters": True, "pool_pre_ping": True}
    WTF_CSRF_ENABLED = False
