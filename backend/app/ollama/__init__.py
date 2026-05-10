"""Ollama idle lifecycle (backend) and HTTP routes."""

from .constants import OLLAMA_IDLE_POLL_STOP_KEY, OLLAMA_IDLE_SERVICE_KEY
from .routes import ollama_bp
from .service import OllamaIdleService

__all__ = [
    "OLLAMA_IDLE_POLL_STOP_KEY",
    "OLLAMA_IDLE_SERVICE_KEY",
    "OllamaIdleService",
    "ollama_bp",
]
