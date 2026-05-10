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

# Run as a non-root user; gunicorn binds to 8000 which does not need privileges.
RUN useradd --create-home --uid 1001 appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).status == 200 else 1)"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "wsgi:app"]
