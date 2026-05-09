"""Pydantic models for a subset of the SRGSSR Articles API v2 JSON (OpenAPI aligned)."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

# --- Shared primitives ---


class TextBlock(BaseModel):
    """``components.schemas.Text``."""

    model_config = ConfigDict(extra="ignore")

    content: str
    language: str | None = None


class UriLocator(BaseModel):
    """``components.schemas.URI``."""

    model_config = ConfigDict(extra="ignore")

    url: str | None = None
    urn: str | None = None


class SrgIdentifier(BaseModel):
    """``components.schemas.Identifier``."""

    model_config = ConfigDict(extra="ignore")

    value: str
    type: str


class AccessCondition(BaseModel):
    """``components.schemas.AccessCondition`` (only ``name`` required by spec)."""

    model_config = ConfigDict(extra="ignore")

    name: str


class ArticleContentBlock(BaseModel):
    """``components.schemas.ArticleContent``."""

    model_config = ConfigDict(extra="ignore")

    text: list[str] = Field(default_factory=list)


class PictureResource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Picture"]
    locator: UriLocator


class DocumentResource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Document"]
    locator: UriLocator
    identifiers: list[SrgIdentifier] = Field(default_factory=list)


class LinkResource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["Link"]
    locator: UriLocator
    name: str | None = None


Resource = Annotated[
    Union[PictureResource, DocumentResource, LinkResource],  # noqa: UP007
    Field(discriminator="type"),
]


class ArticleRecord(BaseModel):
    """``components.schemas.Article`` (fields required by parser + mapping)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    publisher: str
    provenance: str
    accessConditions: list[AccessCondition]
    identifiers: list[SrgIdentifier]
    title: list[TextBlock] | None = None
    lead: list[TextBlock] | None = None
    content: ArticleContentBlock | None = None
    releaseDate: str | None = None
    modificationDate: str | None = None
    resources: list[Resource] | None = None


class ArticleListPage(BaseModel):
    """``components.schemas.ArticlePage``."""

    model_config = ConfigDict(extra="ignore")

    cursor: str | None = None
    results: list[ArticleRecord]
