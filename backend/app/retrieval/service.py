"""Orchestrate Ollama embeddings, ``vectors.db`` KNN, and lexicon filtering."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..ollama.embeddings import OllamaEmbedClient, OllamaEmbedError
from ..ollama.service import OllamaIdleService
from ..sidecar.client import post_ollama_start
from ..vectors.repository import WordEmbeddingsRepository
from ..words.ports import WordsRepositoryPort
from .errors import RetrievalServiceError

DEFAULT_RETRIEVAL_TOP_K = 20
DEFAULT_RETRIEVAL_CONTEXT_MAX_CHARS = 8192
KNN_FETCH_CAP = 500


def _coerce_positive_int(raw: Any, *, default: int) -> int:
    """Return a positive int from settings values; fall back to ``default`` if invalid."""
    if raw is None:
        return default
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return default
    return n if n > 0 else default


class LexiconRetrievalService:
    """Embeds dictionary rows and article context; reads/writes ``WordEmbeddingsRepository``."""

    def __init__(
        self,
        *,
        words_repo: WordsRepositoryPort,
        vectors_repo: WordEmbeddingsRepository,
        embed_client: OllamaEmbedClient,
        settings_row: Callable[[], dict[str, Any]],
        idle_service: OllamaIdleService | None,
        sidecar_base_url: str,
        sidecar_shared_secret: str,
        start_ollama_fn: Callable[[str, str | None], tuple[bool, str | None]] | None = None,
    ) -> None:
        self._words = words_repo
        self._vectors = vectors_repo
        self._embed = embed_client
        self._settings_row = settings_row
        self._idle = idle_service
        self._sidecar_base = sidecar_base_url.strip()
        self._sidecar_secret = sidecar_shared_secret
        self._start_ollama_fn = start_ollama_fn or post_ollama_start

    def embed_and_store_word(self, word_id: int) -> None:
        """Embed ``german_label`` for ``word_id`` and upsert into ``vectors.db``."""
        row = self._words.get(word_id)
        if row is None:
            raise RetrievalServiceError(f"Word id {word_id} not found")
        label = row.get("german_label")
        if not isinstance(label, str) or not label.strip():
            raise RetrievalServiceError("german_label must be a non-empty string")

        def work() -> None:
            vec = self._embed.embed_text(label)
            self._vectors.insert(word_id, vec)

        self._run_tracked_ollama_session(work)

    def top_word_ids_for_context(self, context: str) -> list[int]:
        """Return up to ``k`` lexicon ``word_id`` values nearest the embedded ``context``."""
        if self._words.count_words() == 0:
            return []

        settings = self._settings_row()
        k = _coerce_positive_int(settings.get("retrieval_top_k"), default=DEFAULT_RETRIEVAL_TOP_K)
        max_chars = _coerce_positive_int(
            settings.get("retrieval_context_max_chars"),
            default=DEFAULT_RETRIEVAL_CONTEXT_MAX_CHARS,
        )

        text = context if len(context) <= max_chars else context[:max_chars]

        def work() -> list[int]:
            query_vec = self._embed.embed_text(text)
            fetch_n = min(KNN_FETCH_CAP, max(k * 50, k))
            ranked = self._vectors.knn_by_vector(query_vec, fetch_n)
            return self._filter_ranked_to_lexicon(ranked, k)

        return self._run_tracked_ollama_session(work)

    def _filter_ranked_to_lexicon(
        self,
        ranked: list[tuple[int, float]],
        k: int,
    ) -> list[int]:
        if k <= 0:
            return []
        if not ranked:
            return []
        candidates = [wid for wid, _ in ranked]
        allowed = self._words.ids_in_lexicon(candidates)
        out: list[int] = []
        for wid, _dist in ranked:
            if wid in allowed:
                out.append(wid)
                if len(out) >= k:
                    break
        return out

    def _ensure_ollama_container(self) -> None:
        if not self._sidecar_base:
            return
        ok, err = self._start_ollama_fn(self._sidecar_base, self._sidecar_secret or None)
        if not ok:
            msg = err or "unknown error"
            raise RetrievalServiceError(f"Sidecar Ollama start failed: {msg}")

    def _run_tracked_ollama_session[T](self, work: Callable[[], T]) -> T:
        self._ensure_ollama_container()
        idle = self._idle
        if idle is not None:
            idle.begin_request()
        try:
            return work()
        except OllamaEmbedError as exc:
            raise RetrievalServiceError(str(exc)) from exc
        finally:
            if idle is not None:
                idle.end_request()
