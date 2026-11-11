from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

RunCli = Callable[[list[str]], tuple[int, str, str]]
WriteTree = Callable[[dict[str, str]], Path]
