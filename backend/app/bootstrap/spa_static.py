"""Optional single-page app static file serving from a Vite ``dist`` directory."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, abort, send_from_directory


def register_spa_static_routes(app: Flask) -> None:
    """If ``STATIC_SPA_DIR`` contains ``index.html``, serve the SPA and static assets.

    Registered after API blueprints so ``/api/*`` routes keep precedence. When the
    directory is missing or empty, this is a no-op (local pytest, API-only images).
    """
    raw = app.config.get("STATIC_SPA_DIR")
    if raw is None:
        return
    spa_root = Path(str(raw)).resolve()
    if not (spa_root / "index.html").is_file():
        return

    def _safe_relative_path(request_path: str) -> str | None:
        """Return a path relative to ``spa_root`` or None if outside the tree."""
        rel = request_path.lstrip("/")
        if not rel:
            return ""
        try:
            candidate = (spa_root / rel).resolve()
            candidate.relative_to(spa_root)
        except ValueError:
            return None
        return rel

    @app.get("/")
    def spa_index() -> Response:
        return send_from_directory(spa_root, "index.html")

    @app.get("/<path:requested_path>")
    def spa_or_asset(requested_path: str) -> Response:
        if requested_path == "api" or requested_path.startswith("api/"):
            abort(404)
        rel = _safe_relative_path(requested_path)
        if rel is None:
            abort(404)
        if rel != "":
            file_path = spa_root / rel
            if file_path.is_file():
                return send_from_directory(spa_root, rel)
        return send_from_directory(spa_root, "index.html")
