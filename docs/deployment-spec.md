# Spec: Production Web Deployment

## Objective

Package the Vue and Flask application as one provider-neutral Docker image. The
container serves the compiled frontend and API on one origin, connects to an
external MySQL database, and can run behind a managed HTTPS reverse proxy.

## Tech Stack

- Python 3.12, Flask 3.0.3, Flask-SQLAlchemy 3.1.1
- SQLAlchemy 2.0.31, PyMySQL 1.1.1
- Gunicorn 26.0.0
- Node.js 22, Vue 3.5, Vite 6
- MySQL 8.x outside the application container

## Commands

- Backend tests: `python -m pytest backend/tests -q`
- Frontend build: `npm --prefix frontend run build`
- Image build: `docker build --tag station-ticketing:local .`
- Container run: `docker run --rm --env-file .env -p 8000:8000 station-ticketing:local`
- Initialize empty database: `flask --app run.py init-db`
- Optional demo data: `flask --app run.py seed-demo`

## Project Structure

- `backend/app/`: Flask application, routes, services, and models
- `backend/tests/`: backend behavior and deployment-contract tests
- `frontend/`: Vue source and Vite build configuration
- `sql/`: MySQL bootstrap and incremental migrations
- `Dockerfile`: multi-stage frontend build and Python runtime image
- `.dockerignore`: files excluded from the container build context
- `docs/`: architecture and deployment documentation

## Code Style

Use explicit environment-backed configuration and fail fast on invalid values:

```python
PORT = int(os.getenv("PORT", "8000"))
if PORT <= 0:
    raise ValueError("PORT must be positive")
```

Keep deployment configuration small, typed where practical, and free of secrets.

## Testing Strategy

- Unit tests cover environment normalization and Gunicorn configuration.
- Flask integration tests cover health, readiness, security headers, static
  caching, SPA fallback, and database CLI behavior.
- The full backend suite and Vite production build are release gates.
- A Docker image build is the final packaging check when Docker is available.

## Boundaries

- Always: inject secrets through environment variables, run as a non-root user,
  log to stdout/stderr, and keep the application container stateless.
- Ask first: platform-specific manifests, managed database creation, DNS, TLS,
  destructive schema changes, or publishing an image.
- Never: bake `.env`, database credentials, demo passwords, or database files
  into the image; automatically seed demo accounts in production.

## Success Criteria

- `docker build .` uses the standard `Dockerfile` name and succeeds.
- Gunicorn binds to `0.0.0.0:$PORT` and supports configurable worker settings.
- `/healthz` reports process liveness without requiring the database.
- `/readyz` returns success only when the database connection is usable.
- Hashed frontend assets receive long-lived immutable caching; HTML does not.
- Baseline security headers are present on API and frontend responses.
- `init-db` creates tables without demo users; `seed-demo` is explicit.
- Production dependencies exclude pytest and the image excludes local artifacts.
- Backend tests, Python compilation, and the Vite production build pass.

## Open Questions

- The target provider is unspecified. The artifact is therefore a generic OCI
  image intended for Render, Railway, Fly.io, or a Linux host.
- MySQL provisioning, domain configuration, and TLS termination remain provider
  responsibilities.
