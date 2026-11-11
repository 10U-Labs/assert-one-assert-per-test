from __future__ import annotations

import runpy
import sys
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from test_trees import (
    CLEAN_CRATE,
    CRATE,
    CRATE_FINDINGS,
    FULL_RUN,
    LIBRARY,
    NOTES,
    TESTS,
)

if TYPE_CHECKING:
    from pathlib import Path

    from test_fixture_types import RunCli, WriteTree

UNCLOSED = {LIBRARY: "crate/unclosed.rs"}
MISSING_SEMICOLON = {LIBRARY: "crate/missing_semicolon.rs"}
HIDDEN = {**CLEAN_CRATE, ".cargo/registry/lib.rs": "crate/findings_lib.rs"}
FINDINGS = "\n".join(CRATE_FINDINGS) + "\n"


class TestACleanCrate:
    def test_exits_0(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CLEAN_CRATE)
        assert run_cli(FULL_RUN)[0] == 0

    def test_prints_nothing(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CLEAN_CRATE)
        assert run_cli(FULL_RUN)[1] == ""

    def test_read_from_its_root_exits_0(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_CRATE)
        assert run_cli(["."])[0] == 0

    def test_verbose_counts_the_rust_files(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_CRATE)
        assert "Files scanned: 2" in run_cli([".", "--verbose"])[1]

    def test_skips_a_hidden_directory(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(HIDDEN)
        assert run_cli(["."])[0] == 0


class TestACrateWithFindings:
    def test_exits_1(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CRATE)
        assert run_cli(FULL_RUN)[0] == 1

    def test_prints_every_finding(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CRATE)
        assert run_cli(FULL_RUN)[1] == FINDINGS

    def test_prints_a_file_named_twice_once(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CRATE)
        assert run_cli([*FULL_RUN, LIBRARY])[1] == FINDINGS

    def test_reads_a_glob(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CRATE)
        assert run_cli(["**/*.rs"])[1] == FINDINGS

    def test_reads_a_glob_that_matches_directories(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CRATE)
        assert run_cli(["*"])[1] == FINDINGS

    def test_leaves_out_an_excluded_file(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CRATE)
        assert run_cli([*FULL_RUN, "--exclude", LIBRARY])[1] == f"{CRATE_FINDINGS[-1]}\n"

    def test_verbose_shows_each_finding(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CRATE)
        assert f"  Found: {CRATE_FINDINGS[2]}" in run_cli([*FULL_RUN, "--verbose"])[1]

    def test_count_prints_the_count(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CRATE)
        assert run_cli([*FULL_RUN, "--count"])[1] == f"{len(CRATE_FINDINGS)}\n"

    def test_quiet_prints_nothing(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CRATE)
        assert run_cli([*FULL_RUN, "--quiet"])[1] == ""

    def test_warn_only_exits_0(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CRATE)
        assert run_cli([*FULL_RUN, "--warn-only"])[0] == 0

    def test_fail_fast_stops_after_the_first_file(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CRATE)
        assert run_cli([*FULL_RUN, "--fail-fast"])[1] == "\n".join(CRATE_FINDINGS[:4]) + "\n"


class TestAnUnsupportedFile:
    def test_named_alone_is_not_scanned(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CRATE)
        assert run_cli([NOTES, "--verbose"])[1].endswith("Files scanned: 0\nFindings: 0\n")

    def test_named_alone_is_reported_as_skipped(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CRATE)
        stdout = run_cli([NOTES, "--verbose"])[1]
        assert f"Skipping (unsupported language): {NOTES}" in stdout

    def test_named_alone_exits_0(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CRATE)
        assert run_cli([NOTES])[0] == 0


class TestAFileThatWillNotParse:
    def test_exits_2(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(UNCLOSED)
        assert run_cli(["src"])[0] == 2

    def test_names_the_line_of_the_error(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(UNCLOSED)
        assert run_cli(["src"])[2] == f"Syntax error in {LIBRARY}: line 1\n"

    def test_names_the_line_of_a_missing_token(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(MISSING_SEMICOLON)
        assert run_cli(["src"])[2] == f"Syntax error in {LIBRARY}: line 3\n"


class TestAPathThatIsNotThere:
    def test_exits_2(self, run_cli: RunCli) -> None:
        assert run_cli(["/nonexistent/lib.rs"])[0] == 2

    def test_is_reported(self, run_cli: RunCli) -> None:
        assert run_cli(["/nonexistent/lib.rs"])[2] == "Error: Path not found: /nonexistent/lib.rs\n"

    def test_a_glob_that_matches_nothing_exits_2(self, run_cli: RunCli) -> None:
        assert run_cli(["/nonexistent/*.rs"])[0] == 2

    def test_beside_a_clean_crate_exits_2(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_CRATE)
        assert run_cli([*FULL_RUN, "/nonexistent/lib.rs"])[0] == 2

    def test_beside_a_clean_crate_is_named_in_the_summary(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_CRATE)
        stdout = run_cli([*FULL_RUN, "/nonexistent/lib.rs", "--verbose", "--exclude", TESTS])[1]
        assert stdout.endswith("Errors occurred during scanning.\n")

    @pytest.mark.usefixtures("broken_symlink")
    def test_a_broken_symlink_matched_by_a_glob_is_passed_over(
        self, tmp_path: Path, run_cli: RunCli
    ) -> None:
        assert run_cli([f"{tmp_path}/*.rs"])[0] == 0


class TestAFileThatCannotBeRead:
    def test_exits_2(self, unreadable_file: Path, run_cli: RunCli) -> None:
        assert run_cli([str(unreadable_file)])[0] == 2

    def test_is_reported(self, unreadable_file: Path, run_cli: RunCli) -> None:
        assert run_cli([str(unreadable_file)])[2].startswith(f"Error reading {unreadable_file}")


class TestTheModule:
    def test_calls_main_once(self) -> None:
        with patch("assert_one_assert_per_test.cli.main") as entry_point:
            sys.modules.pop("assert_one_assert_per_test.__main__", None)
            runpy.run_module("assert_one_assert_per_test", run_name="__main__")
        assert entry_point.call_count == 1

    def test_reads_the_arguments_it_was_run_with(self, write_tree: WriteTree) -> None:
        write_tree(CRATE)
        sys.modules.pop("assert_one_assert_per_test.__main__", None)
        with patch.object(sys, "argv", ["assert-one-assert-per-test", *FULL_RUN]):
            with pytest.raises(SystemExit, match="^1$"):
                runpy.run_module("assert_one_assert_per_test", run_name="__main__")
