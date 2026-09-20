ARG NODE_IMAGE=node:22-alpine
ARG PYTHON_IMAGE=python:3.12-slim

FROM ${NODE_IMAGE} AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


FROM ${PYTHON_IMAGE} AS runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-log-init --create-home app

COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --requirement /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY --chown=app:app backend/ /app/backend/
COPY --from=frontend-builder --chown=app:app /build/frontend/dist/ /app/frontend/dist/

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/healthz', timeout=2).close()"

CMD ["gunicorn", "--config", "/app/backend/gunicorn.conf.py", "--chdir", "/app/backend", "run:app"]
