from __future__ import annotations

import os


def positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


bind = f"0.0.0.0:{positive_int('PORT', 8000)}"
workers = positive_int("WEB_CONCURRENCY", 2)
threads = positive_int("WEB_THREADS", 2)
worker_class = "gthread"

timeout = positive_int("WEB_TIMEOUT", 30)
graceful_timeout = positive_int("WEB_GRACEFUL_TIMEOUT", 30)
keepalive = positive_int("WEB_KEEPALIVE", 5)
max_requests = positive_int("WEB_MAX_REQUESTS", 1000)
max_requests_jitter = positive_int("WEB_MAX_REQUESTS_JITTER", 100)

accesslog = "-"
errorlog = "-"
capture_output = True
