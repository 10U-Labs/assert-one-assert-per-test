from __future__ import annotations

from assert_one_assert_per_test import rust
from assert_one_assert_per_test.finding import Finding, Unparsable
from assert_one_assert_per_test.scanner import scanner_for


class TestScannerFor:
    def test_reads_rust_with_the_rust_scanner(self) -> None:
        assert scanner_for("src/lib.rs") is rust.scan

    def test_has_no_scanner_for_an_unsupported_language(self) -> None:
        assert scanner_for("test_example.py") is None

    def test_has_no_scanner_for_a_file_without_a_suffix(self) -> None:
        assert scanner_for("Makefile") is None


class TestFinding:
    def test_formats_a_count_finding(self) -> None:
        assert str(Finding("src/lib.rs", 2, "adds", 0)) == "src/lib.rs:2:adds:0"

    def test_formats_a_conjunction_finding(self) -> None:
        finding = Finding("src/lib.rs", 3, "adds", 2, True)
        assert str(finding) == "src/lib.rs:3:adds:2:conjunction"


class TestUnparsable:
    def test_names_the_line(self) -> None:
        assert str(Unparsable(7)) == "line 7"

    def test_keeps_the_line_number(self) -> None:
        assert Unparsable(7).line_number == 7
