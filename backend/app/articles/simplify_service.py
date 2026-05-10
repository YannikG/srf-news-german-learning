"""Orchestrate simplify: retrieval, streamed LLM, SSE, persistence (P5-I03)."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any, Protocol

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from ..ollama.chat_stream import OllamaChatStreamError, OllamaChatStreamIncompleteError
from ..ollama.service import OllamaIdleService
from ..retrieval.errors import RetrievalServiceError
from ..retrieval.service import LexiconRetrievalService
from ..words.ports import WordsRepositoryPort
from .ports import ArticlesRepositoryPort
from .simplify_markdown import strip_images_from_markdown
from .simplify_models import SimplifyLlmOutputModel
from .simplify_repository import SqliteArticleSimplifyRepository

logger = logging.getLogger(__name__)

_ALLOWED_CEFR = frozenset({"A1", "A2", "B1", "B2", "C1", "C2"})


class _SsePublishPort(Protocol):
    def publish(self, event: str, data: dict[str, object]) -> None: ...


class _ChatStreamPort(Protocol):
    def stream_assistant_text(self, *, system: str, user: str) -> Iterator[str]: ...


class ArticleSimplifyServiceError(Exception):
    """Domain error for simplify flow (HTTP status in ``status_code``)."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _extract_json_object(raw: str) -> str:
    """Take the first JSON object from model text, tolerating a fenced block.

    Uses :meth:`json.JSONDecoder.raw_decode` so braces inside JSON strings do not
    truncate the payload (unlike a naive ``rfind('}')`` slice).
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if not lines:
            raise ArticleSimplifyServiceError("LLM response is empty", 502)
        inner = lines[1:]
        while inner and inner[-1].strip() in {"", "```"}:
            inner.pop()
        text = "\n".join(inner).strip()
    start = text.find("{")
    if start == -1:
        raise ArticleSimplifyServiceError("LLM response did not contain a JSON object", 502)
    decoder = json.JSONDecoder()
    try:
        _, end = decoder.raw_decode(text, start)
    except json.JSONDecodeError as exc:
        raise ArticleSimplifyServiceError("LLM response is not valid JSON", 502) from exc
    return text[start:end]


def _build_prompts(
    *,
    cefr_level: str,
    markdown_original: str,
    lexicon_snippets: list[dict[str, Any]],
) -> tuple[str, str]:
    system = (
        "You rewrite Swiss German news articles for language learners. "
        f"Target CEFR level: {cefr_level}. "
        "Respond with a single JSON object only (no prose before or after). "
        "The JSON must match this shape: "
        '{"markdown": string, "used_word_ids": number[], "suggestions": '
        '[{"german_label": string, "translation": string, "category": string}]} '
        "Use between 3 and 4 suggestions. "
        "used_word_ids must be a subset of the word ids listed in the user message. "
        "markdown must be plain learner-friendly Markdown without images or figures."
    )
    user_payload = {
        "article_markdown": markdown_original,
        "lexicon_words": lexicon_snippets,
    }
    user = json.dumps(user_payload, ensure_ascii=False)
    return system, user


class ArticleSimplifyService:
    """Runs retrieval, streams the LLM, publishes SSE, persists rows."""

    def __init__(
        self,
        *,
        articles_repo: ArticlesRepositoryPort,
        words_repo: WordsRepositoryPort,
        simplify_repo: SqliteArticleSimplifyRepository,
        retrieval: LexiconRetrievalService,
        chat_client: _ChatStreamPort,
        sse_hub: _SsePublishPort,
        idle_service: OllamaIdleService | None,
    ) -> None:
        self._articles = articles_repo
        self._words = words_repo
        self._simplify_repo = simplify_repo
        self._retrieval = retrieval
        self._chat = chat_client
        self._hub = sse_hub
        self._idle = idle_service

    def simplify_article(self, article_id: int, cefr_level: str) -> dict[str, Any]:
        """Execute simplify pipeline; returns a JSON-serializable summary."""
        cefr = cefr_level.strip().upper()
        if cefr not in _ALLOWED_CEFR:
            raise ArticleSimplifyServiceError("cefr_level must be one of A1,A2,B1,B2,C1,C2", 400)

        row = self._articles.get(article_id)
        if row is None:
            raise ArticleSimplifyServiceError("Article not found", 404)

        markdown_original = row.get("markdown_original")
        if not isinstance(markdown_original, str):
            raise ArticleSimplifyServiceError("Article markdown is missing", 500)

        idle = self._idle
        if idle is not None:
            idle.begin_request()
        try:
            return self._simplify_inner(article_id, cefr, markdown_original)
        finally:
            if idle is not None:
                idle.end_request()

    def _simplify_inner(
        self,
        article_id: int,
        cefr_level: str,
        markdown_original: str,
    ) -> dict[str, Any]:
        try:
            top_ids = self._retrieval.top_word_ids_for_context(
                markdown_original,
                track_idle=False,
            )
        except RetrievalServiceError as exc:
            logger.warning("Retrieval failed for simplify: %s", exc)
            raise ArticleSimplifyServiceError(str(exc), 502) from exc

        snippets: list[dict[str, Any]] = []
        for wid in top_ids:
            w = self._words.get(wid)
            if w is None:
                continue
            label = w.get("german_label")
            if isinstance(label, str) and label.strip():
                snippets.append({"id": wid, "german_label": label.strip()})

        system, user = _build_prompts(
            cefr_level=cefr_level,
            markdown_original=markdown_original,
            lexicon_snippets=snippets,
        )

        parts: list[str] = []
        try:
            stream_it: Iterator[str] = self._chat.stream_assistant_text(
                system=system,
                user=user,
            )
            for chunk in stream_it:
                parts.append(chunk)
                self._hub.publish(
                    "llm_chunk",
                    {"article_id": article_id, "delta": chunk},
                )
        except OllamaChatStreamIncompleteError as exc:
            raise ArticleSimplifyServiceError("LLM stream ended prematurely", 502) from exc
        except OllamaChatStreamError as exc:
            raise ArticleSimplifyServiceError(str(exc), 502) from exc

        raw = "".join(parts)
        try:
            doc = _extract_json_object(raw)
            parsed = SimplifyLlmOutputModel.model_validate_json(doc)
        except (ValidationError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ArticleSimplifyServiceError("LLM output failed validation", 502) from exc

        markdown_clean = strip_images_from_markdown(parsed.markdown)
        if "!" in markdown_clean and "](" in markdown_clean:
            # Cheap guard if Markdown image syntax survived unusual whitespace.
            markdown_clean = strip_images_from_markdown(markdown_clean)

        allowed_ids = self._words.ids_in_lexicon(parsed.used_word_ids)
        used_ordered = [wid for wid in parsed.used_word_ids if wid in allowed_ids]

        new_word_rows: list[dict[str, str | None]] = []
        for suggestion in parsed.suggestions:
            new_word_rows.append(
                {
                    "german_label": suggestion.german_label,
                    "category": suggestion.category.strip() or "suggestion",
                    "difficulty": "Neu",
                    "translation": suggestion.translation.strip(),
                    "cefr_level": cefr_level,
                },
            )

        try:
            sid, suggested_ids = self._simplify_repo.replace_simplification_with_new_words(
                article_id=article_id,
                cefr_level=cefr_level,
                markdown_simplified=markdown_clean,
                used_word_ids=used_ordered,
                new_words=new_word_rows,
            )
        except SQLAlchemyError as exc:
            logger.exception("Simplify persistence failed")
            raise ArticleSimplifyServiceError("Failed to persist simplification", 500) from exc
        except (TypeError, ValueError, KeyError) as exc:
            raise ArticleSimplifyServiceError("Failed to persist simplification", 500) from exc

        for wid in suggested_ids:
            try:
                self._retrieval.embed_and_store_word(wid, track_idle=False)
            except RetrievalServiceError as exc:
                logger.warning("Embedding suggestion word %s failed: %s", wid, exc)
                raise ArticleSimplifyServiceError(str(exc), 502) from exc

        self._hub.publish(
            "llm_done",
            {
                "article_id": article_id,
                "cefr_level": cefr_level,
                "simplification_id": sid,
            },
        )

        return {
            "simplification_id": sid,
            "article_id": article_id,
            "cefr_level": cefr_level,
            "markdown_simplified": markdown_clean,
            "used_word_ids": used_ordered,
            "suggested_word_ids": suggested_ids,
        }
