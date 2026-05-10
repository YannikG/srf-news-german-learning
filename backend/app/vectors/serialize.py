"""Float32 vector blob encoding (vec0 wire format, stdlib only)."""

from __future__ import annotations

import struct
from collections.abc import Sequence


def pack_float32(vector: Sequence[float]) -> bytes:
    """Pack ``vector`` as little-endian float32 values (same layout sqlite-vec expects)."""
    return struct.pack(f"<{len(vector)}f", *vector)
