# Build from repository root (see compose.yaml: context ``.``, dockerfile ``backend/Dockerfile``).
# Debian bookworm (glibc): PyPI ``sqlite-vec`` ships manylinux wheels for linux/amd64
# and linux/arm64. Alpine/musl is avoided because those wheels do not apply.

FROM node:20-bookworm-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY backend/wsgi.py ./
COPY --from=frontend-build /frontend/dist ./app/static/spa

RUN useradd --create-home --uid 1001 appuser \
 && chown -R appuser:appuser /app \
 && apt-get update \
 && apt-get install -y --no-install-recommends gosu \
 && rm -rf /var/lib/apt/lists/*

COPY backend/docker-entrypoint-web.sh /docker-entrypoint-web.sh
RUN chmod +x /docker-entrypoint-web.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD gosu appuser python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).status == 200 else 1)"

ENTRYPOINT ["/docker-entrypoint-web.sh"]
# ``--timeout 0``: avoid killing workers during long-lived SSE (``GET /api/events/stream``).
# ``gthread``: each worker process serves many concurrent requests on threads; one thread can
# hold the SSE stream while others still answer ``GET /api/health`` and the rest of the API.
# Rapid browser reloads otherwise open several EventSources briefly and exhaust pure ``sync``
# workers (everything queues until the 15s client health timeout).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-k", "gthread", "--workers", "2", "--threads", "16", "--timeout", "0", "wsgi:app"]
