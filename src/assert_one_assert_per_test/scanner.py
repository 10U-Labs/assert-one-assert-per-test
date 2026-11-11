from __future__ import annotations

import os
from collections.abc import Callable

from . import rust
from .finding import Finding

Scanner = Callable[[str, bytes], list[Finding]]

SCANNERS: dict[str, Scanner] = {
    ".rs": rust.scan,
}


def scanner_for(path: str) -> Scanner | None:
    return SCANNERS.get(os.path.splitext(path)[1])
