"""Concrete upstream adapters for :class:`~app.news.upstream_port.NewsIngestUpstreamPort`."""

from __future__ import annotations

from .newsapi_upstream import NewsApiUpstreamAdapter
from .srgssr_upstream import SrgSsrNewsUpstreamAdapter

__all__ = ["NewsApiUpstreamAdapter", "SrgSsrNewsUpstreamAdapter"]
