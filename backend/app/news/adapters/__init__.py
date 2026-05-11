"""Concrete upstream adapters for :class:`~app.news.upstream_port.NewsIngestUpstreamPort`."""

from __future__ import annotations

from .srgssr_upstream import SrgSsrNewsUpstreamAdapter

__all__ = ["SrgSsrNewsUpstreamAdapter"]
