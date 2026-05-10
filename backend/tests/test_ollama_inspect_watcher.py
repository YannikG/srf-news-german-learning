"""Inspect watcher generation invalidates stale SSE publisher threads."""

from app.ollama.inspect_watcher import bump_ollama_inspect_watcher_generation


def test_inspect_watcher_generation_monotonic() -> None:
    a = bump_ollama_inspect_watcher_generation()
    b = bump_ollama_inspect_watcher_generation()
    assert b == a + 1
