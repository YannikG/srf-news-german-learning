"""Migration runner edge cases."""

from __future__ import annotations

import pytest

from app.db.runner import _migration_bookkeeping_sql


def test_migration_id_rejects_unsafe_stems() -> None:
    with pytest.raises(ValueError, match="migration_id must match"):
        _migration_bookkeeping_sql("../../../x")
