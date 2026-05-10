# Sidecar: Docker socket access requires a user that can read /var/run/docker.sock.
# For local Compose this image runs as root; do not expose the sidecar port publicly.
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY server.py wsgi.py ./

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8090/health', timeout=3); sys.exit(0 if r.status==200 else 1)"

# Several sync workers so a long ``docker stop`` on one request does not block all
# concurrent ``/ollama/inspect`` calls from the web app (health + watcher probes).
CMD ["gunicorn", "--bind", "0.0.0.0:8090", "--workers", "4", "wsgi:app"]
