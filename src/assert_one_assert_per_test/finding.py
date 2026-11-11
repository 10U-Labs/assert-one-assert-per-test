from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    path: str
    line_number: int
    function_name: str
    assert_count: int
    conjunction: bool = False

    def __str__(self) -> str:
        suffix = ":conjunction" if self.conjunction else ""
        return (
            f"{self.path}:{self.line_number}:{self.function_name}"
            f":{self.assert_count}{suffix}"
        )


class Unparsable(Exception):
    def __init__(self, line_number: int) -> None:
        super().__init__(f"line {line_number}")
        self.line_number = line_number
