"""Pydantic models for LLM simplify JSON output (P5-I03)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class SimplifySuggestionModel(BaseModel):
    """One learner vocabulary suggestion from the model."""

    german_label: str = Field(min_length=1, max_length=500)
    translation: str = Field(default="", max_length=2000)
    category: str = Field(default="suggestion", max_length=200)

    @field_validator("german_label")
    @classmethod
    def strip_label(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("german_label must not be empty")
        return s


class SimplifyLlmOutputModel(BaseModel):
    """Structured JSON the model must emit after streaming completes."""

    markdown: str = Field(default="", max_length=500_000)
    used_word_ids: list[int] = Field(default_factory=list)
    suggestions: list[SimplifySuggestionModel] = Field(min_length=3, max_length=4)
