"""OpenCV policies: consumer modules have pinned Core declaration references."""
from __future__ import annotations

from ..errors import EnhancementError


def assert_external_identity(actual: str, expected: str) -> None:
    if actual != expected:
        raise EnhancementError("OpenCV Core external source revision differs from qualified pin")
