"""Flask application package.

``create_app`` is defined under ``app.bootstrap`` and re-exported here.
"""

from __future__ import annotations

from .bootstrap.factory import create_app

__all__ = ["create_app"]
