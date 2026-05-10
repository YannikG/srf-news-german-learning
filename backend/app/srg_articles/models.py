"""Pydantic models for a subset of the SRGSSR Articles API v2 JSON (OpenAPI aligned).

API keys stay camelCase in JSON; Python attributes use snake_case with ``Field(alias=...)``.
``populate_by_name=True`` erlaubt Initialisierung mit Alias oder Feldnamen. Die Ressourcen-Union
nutzt unter Python 3.10+ den ``|``-Operator (wie in CI); unter 3.9 ``typing.Union`` (Import).
"""

from __future__ import annotations

import sys
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

# --- Shared primitives ---

_MODEL_CFG = ConfigDict(extra="ignore", populate_by_name=True)


class TextBlock(BaseModel):
    """``components.schemas.Text``."""

    model_config = _MODEL_CFG

    content: str
    language: str | None = None


class UriLocator(BaseModel):
    """``components.schemas.URI``."""

    model_config = _MODEL_CFG

    url: str | None = None
    urn: str | None = None


class SrgIdentifier(BaseModel):
    """``components.schemas.Identifier``."""

    model_config = _MODEL_CFG

    value: str
    identifier_type: str = Field(alias="type")


class AccessCondition(BaseModel):
    """``components.schemas.AccessCondition`` (only ``name`` required by spec)."""

    model_config = _MODEL_CFG

    name: str


class ArticleContentBlock(BaseModel):
    """``components.schemas.ArticleContent``."""

    model_config = _MODEL_CFG

    text: list[str] = Field(default_factory=list)


class PictureResource(BaseModel):
    model_config = _MODEL_CFG

    type: Literal["Picture"]
    locator: UriLocator


class DocumentResource(BaseModel):
    model_config = _MODEL_CFG

    type: Literal["Document"]
    locator: UriLocator
    identifiers: list[SrgIdentifier] = Field(default_factory=list)


class LinkResource(BaseModel):
    model_config = _MODEL_CFG

    type: Literal["Link"]
    locator: UriLocator
    name: str | None = None


# Unter 3.9 schlägt ``Metaclass | Metaclass`` beim Import fehl; ab 3.10 wie in CI der ``|``-Zweig.
if sys.version_info >= (3, 10):  # noqa: UP036
    _ResourceUnion = PictureResource | DocumentResource | LinkResource
else:
    _ResourceUnion = Union[PictureResource, DocumentResource, LinkResource]  # noqa: UP007

Resource = Annotated[_ResourceUnion, Field(discriminator="type")]


class ArticleRecord(BaseModel):
    """``components.schemas.Article`` (fields required by parser + mapping)."""

    model_config = _MODEL_CFG

    id: str
    publisher: str
    provenance: str
    access_conditions: list[AccessCondition] = Field(alias="accessConditions")
    identifiers: list[SrgIdentifier]
    title: list[TextBlock] | None = None
    lead: list[TextBlock] | None = None
    content: ArticleContentBlock | None = None
    release_date: str | None = Field(default=None, alias="releaseDate")
    modification_date: str | None = Field(default=None, alias="modificationDate")
    resources: list[Resource] | None = None


class ArticleListPage(BaseModel):
    """``components.schemas.ArticlePage``."""

    model_config = _MODEL_CFG

    cursor: str | None = None
    results: list[ArticleRecord]
