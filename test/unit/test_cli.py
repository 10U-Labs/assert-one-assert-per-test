from __future__ import annotations

import importlib
import sys
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from assert_one_assert_per_test.cli import (
    ScanResult,
    _expand_directory,
    _expand_glob,
    _is_glob_pattern,
    _iter_files,
    _should_skip_file,
    create_parser,
    determine_exit_code,
    output_findings,
    parse_patterns,
    process_files,
)
from assert_one_assert_per_test.finding import Finding

if TYPE_CHECKING:
    from test_fixture_types import RunCli, WriteTree

CLEAN = {"src/lib.rs": "cli/clean.rs"}
FINDING = {"src/lib.rs": "cli/finding.rs"}
TWO_FINDINGS = {"src/a.rs": "cli/finding.rs", "src/b.rs": "cli/finding.rs"}
BROKEN = {"src/lib.rs": "cli/broken.rs"}
NOTES = {"src/notes.txt": "cli/notes.txt"}
A_FINDING = Finding("src/lib.rs", 2, "finding", 0)


class TestCreateParser:
    def test_requires_files_argument(self) -> None:
        with pytest.raises(SystemExit):
            create_parser().parse_args([])

    def test_accepts_multiple_files(self) -> None:
        args = create_parser().parse_args(["a.rs", "b.rs"])
        assert args.files == ["a.rs", "b.rs"]

    def test_accepts_exclude_option(self) -> None:
        args = create_parser().parse_args(["src", "--exclude", "*/target/*"])
        assert args.exclude == "*/target/*"

    @pytest.mark.parametrize(
        "flag", ["quiet", "count", "verbose", "fail_fast", "warn_only"]
    )
    def test_sets_each_flag(self, flag: str) -> None:
        args = create_parser().parse_args(["src", f"--{flag.replace('_', '-')}"])
        assert getattr(args, flag) is True

    def test_output_modes_are_mutually_exclusive(self) -> None:
        with pytest.raises(SystemExit):
            create_parser().parse_args(["src", "--quiet", "--count"])

    def test_behavior_modes_are_mutually_exclusive(self) -> None:
        with pytest.raises(SystemExit):
            create_parser().parse_args(["src", "--fail-fast", "--warn-only"])

    def test_help_names_the_supported_suffixes(self) -> None:
        assert "(.rs)" in create_parser().format_help()


class TestParsePatterns:
    def test_returns_empty_for_none(self) -> None:
        assert parse_patterns(None) == []

    def test_returns_empty_for_empty_string(self) -> None:
        assert parse_patterns("") == []

    def test_parses_multiple_patterns(self) -> None:
        assert parse_patterns("*.rs,target/*") == ["*.rs", "target/*"]

    def test_strips_whitespace(self) -> None:
        assert parse_patterns(" *.rs , target/* ") == ["*.rs", "target/*"]

    def test_ignores_empty_entries(self) -> None:
        assert parse_patterns("*.rs,,target/*,") == ["*.rs", "target/*"]


class TestIsGlobPattern:
    @pytest.mark.parametrize("pattern", ["*.rs", "lib?.rs", "lib[0-9].rs"])
    def test_detects_a_wildcard(self, pattern: str) -> None:
        assert _is_glob_pattern(pattern) is True

    def test_regular_path_is_not_glob(self) -> None:
        assert _is_glob_pattern("src/lib.rs") is False


class TestExpandDirectory:
    def test_finds_rust_files(self, tmp_path: Path) -> None:
        (tmp_path / "lib.rs").write_bytes(b"")
        assert len(_expand_directory(str(tmp_path))) == 1

    def test_ignores_unsupported_files(self, tmp_path: Path) -> None:
        (tmp_path / "notes.txt").write_bytes(b"")
        assert not _expand_directory(str(tmp_path))

    def test_recurses_into_subdirectories(self, tmp_path: Path) -> None:
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "cli.rs").write_bytes(b"")
        assert len(_expand_directory(str(tmp_path))) == 1

    def test_skips_hidden_directories(self, tmp_path: Path) -> None:
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".hidden" / "lib.rs").write_bytes(b"")
        assert not _expand_directory(str(tmp_path))


class TestExpandGlob:
    def test_returns_matching_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.rs").write_bytes(b"")
        (tmp_path / "b.rs").write_bytes(b"")
        assert len(_expand_glob(f"{tmp_path}/*.rs")[0]) == 2

    def test_reports_a_match_was_found(self, tmp_path: Path) -> None:
        (tmp_path / "a.rs").write_bytes(b"")
        assert _expand_glob(f"{tmp_path}/*.rs")[1] is True

    def test_returns_no_files_for_no_matches(self) -> None:
        assert not _expand_glob("/nonexistent/path/*.rs")[0]

    def test_reports_no_match_was_found(self) -> None:
        assert _expand_glob("/nonexistent/path/*.rs")[1] is False

    def test_expands_matched_directories(self, tmp_path: Path) -> None:
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "cli.rs").write_bytes(b"")
        assert len(_expand_glob(f"{tmp_path}/test*")[0]) == 1

    @pytest.mark.usefixtures("broken_symlink")
    def test_ignores_a_match_that_is_neither_file_nor_directory(
        self, tmp_path: Path
    ) -> None:
        assert not _expand_glob(f"{tmp_path}/*.rs")[0]

    @pytest.mark.usefixtures("broken_symlink")
    def test_reports_a_match_for_a_broken_symlink(self, tmp_path: Path) -> None:
        assert _expand_glob(f"{tmp_path}/*.rs")[1] is True


class TestIterFiles:
    def test_handles_a_single_file(self, tmp_path: Path) -> None:
        (tmp_path / "lib.rs").write_bytes(b"")
        assert _iter_files([str(tmp_path / "lib.rs")]) == (
            [str(tmp_path / "lib.rs")],
            [],
        )

    def test_handles_a_directory(self, tmp_path: Path) -> None:
        (tmp_path / "lib.rs").write_bytes(b"")
        assert len(_iter_files([str(tmp_path)])[0]) == 1

    def test_handles_a_glob_pattern(self, tmp_path: Path) -> None:
        (tmp_path / "a.rs").write_bytes(b"")
        (tmp_path / "b.rs").write_bytes(b"")
        assert len(_iter_files([f"{tmp_path}/*.rs"])[0]) == 2

    def test_reports_a_missing_path(self) -> None:
        assert _iter_files(["/nonexistent/lib.rs"]) == ([], ["/nonexistent/lib.rs"])

    def test_reports_a_missing_glob(self) -> None:
        assert _iter_files(["/nonexistent/*.rs"]) == ([], ["/nonexistent/*.rs"])

    def test_deduplicates_files(self, tmp_path: Path) -> None:
        (tmp_path / "lib.rs").write_bytes(b"")
        path = str(tmp_path / "lib.rs")
        assert len(_iter_files([path, path])[0]) == 1


class TestShouldSkipFile:
    def test_no_patterns_returns_false(self) -> None:
        assert _should_skip_file("src/lib.rs", []) is False

    def test_matches_full_path(self) -> None:
        assert _should_skip_file("target/out.rs", ["target/*"]) is True

    def test_matches_filename(self) -> None:
        assert _should_skip_file("src/build.rs", ["build.rs"]) is True

    def test_no_match_returns_false(self) -> None:
        assert _should_skip_file("src/lib.rs", ["build.rs"]) is False


class TestProcessFiles:
    def test_counts_the_scanned_file(self, write_tree: WriteTree) -> None:
        write_tree(FINDING)
        assert process_files(["src/lib.rs"], []).files_scanned == 1

    def test_reports_the_finding(self, write_tree: WriteTree) -> None:
        write_tree(FINDING)
        assert process_files(["src/lib.rs"], []).findings == [A_FINDING]

    def test_skips_unsupported_files(self, write_tree: WriteTree) -> None:
        write_tree(NOTES)
        assert process_files(["src/notes.txt"], []).files_scanned == 0

    def test_respects_exclude_patterns(self, write_tree: WriteTree) -> None:
        write_tree(FINDING)
        assert process_files(["src/lib.rs"], ["src/*"]).files_scanned == 0

    def test_a_syntax_error_sets_had_error(self, write_tree: WriteTree) -> None:
        write_tree(BROKEN)
        assert process_files(["src/lib.rs"], []).had_error is True

    def test_a_syntax_error_is_reported(
        self, write_tree: WriteTree, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write_tree(BROKEN)
        process_files(["src/lib.rs"], [])
        assert "Syntax error in src/lib.rs: line 1" in capsys.readouterr().err

    def test_fail_fast_stops_after_the_first_finding(
        self, write_tree: WriteTree
    ) -> None:
        write_tree(TWO_FINDINGS)
        result = process_files(["src/a.rs", "src/b.rs"], [], fail_fast=True)
        assert len(result.findings) == 1

    def test_verbose_shows_scanning(
        self, write_tree: WriteTree, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write_tree(CLEAN)
        process_files(["src/lib.rs"], [], verbose=True)
        assert "Scanning: src/lib.rs" in capsys.readouterr().out

    def test_verbose_shows_excluded(
        self, write_tree: WriteTree, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write_tree(CLEAN)
        process_files(["src/lib.rs"], ["src/*"], verbose=True)
        assert "Skipping (excluded): src/lib.rs" in capsys.readouterr().out

    def test_verbose_shows_unsupported(
        self, write_tree: WriteTree, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write_tree(NOTES)
        process_files(["src/notes.txt"], [], verbose=True)
        assert "Skipping (unsupported language)" in capsys.readouterr().out

    def test_verbose_shows_findings(
        self, write_tree: WriteTree, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write_tree(FINDING)
        process_files(["src/lib.rs"], [], verbose=True)
        assert f"  Found: {A_FINDING}" in capsys.readouterr().out

    def test_read_error_sets_had_error(self, unreadable_file: Path) -> None:
        assert process_files([str(unreadable_file)], []).had_error is True

    def test_read_error_is_reported(
        self, unreadable_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        process_files([str(unreadable_file)], [])
        assert "Error reading" in capsys.readouterr().err


class TestOutputFindings:
    def test_outputs_every_finding(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([A_FINDING, Finding("src/lib.rs", 7, "other", 2)])
        assert capsys.readouterr().out == "src/lib.rs:2:finding:0\nsrc/lib.rs:7:other:2\n"

    def test_count_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([A_FINDING], count_mode=True)
        assert capsys.readouterr().out == "1\n"


class TestDetermineExitCode:
    def test_returns_0_for_no_findings(self) -> None:
        assert determine_exit_code(ScanResult([], 1, False)) == 0

    def test_returns_1_for_findings(self) -> None:
        assert determine_exit_code(ScanResult([A_FINDING], 1, False)) == 1

    def test_returns_1_for_findings_and_an_error(self) -> None:
        assert determine_exit_code(ScanResult([A_FINDING], 1, True)) == 1

    def test_returns_2_for_an_error(self) -> None:
        assert determine_exit_code(ScanResult([], 0, True)) == 2

    def test_warn_only_returns_0(self) -> None:
        assert determine_exit_code(ScanResult([A_FINDING], 1, False), True) == 0


class TestMain:
    def test_exits_0_for_a_clean_tree(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN)
        assert run_cli(["src"])[0] == 0

    def test_exits_1_for_findings(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(FINDING)
        assert run_cli(["src"])[0] == 1

    def test_exits_2_for_a_missing_path(self, run_cli: RunCli) -> None:
        assert run_cli(["/nonexistent/lib.rs"])[0] == 2

    def test_reports_a_missing_path(self, run_cli: RunCli) -> None:
        assert "Path not found" in run_cli(["/nonexistent/lib.rs"])[2]

    def test_exits_2_when_a_found_file_will_not_parse(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(BROKEN)
        assert run_cli(["src"])[0] == 2

    def test_a_missing_path_beside_a_clean_file_exits_2(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN)
        assert run_cli(["src", "/nonexistent/lib.rs"])[0] == 2

    def test_prints_the_findings(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(FINDING)
        assert run_cli(["src"])[1] == f"{A_FINDING}\n"

    def test_verbose_shows_the_file_count(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN)
        assert "Scanning 1 file(s) for tests..." in run_cli(["src", "--verbose"])[1]

    def test_verbose_shows_files_scanned(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN)
        assert "Files scanned: 1" in run_cli(["src", "--verbose"])[1]

    def test_verbose_shows_the_exclude_patterns(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN)
        stdout = run_cli(["src", "--verbose", "--exclude", "*/target/*"])[1]
        assert "Excluding patterns: */target/*" in stdout

    def test_verbose_shows_errors(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CLEAN)
        stdout = run_cli(["src", "/nonexistent/lib.rs", "--verbose"])[1]
        assert "Errors occurred during scanning." in stdout

    def test_quiet_prints_nothing(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(FINDING)
        assert run_cli(["src", "--quiet"])[1] == ""

    def test_count_prints_the_count(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(FINDING)
        assert run_cli(["src", "--count"])[1] == "1\n"

    def test_warn_only_exits_0(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(FINDING)
        assert run_cli(["src", "--warn-only"])[0] == 0

    def test_fail_fast_prints_one_finding(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(TWO_FINDINGS)
        assert len(run_cli(["src", "--fail-fast"])[1].splitlines()) == 1


class TestMainModule:
    def test_runs_main_once(self) -> None:
        with patch("assert_one_assert_per_test.cli.main") as mock_main:
            sys.modules.pop("assert_one_assert_per_test.__main__", None)
            importlib.import_module("assert_one_assert_per_test.__main__")
        assert mock_main.call_count == 1

    def test_main_is_the_console_script(self) -> None:
        (script,) = entry_points(group="console_scripts", name="assert-one-assert-per-test")
        assert script.value == "assert_one_assert_per_test.cli:main"
