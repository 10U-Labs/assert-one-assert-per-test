from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from test_trees import CLEAN_CRATE, CRATE, CRATE_FINDINGS, FULL_RUN, LIBRARY

if TYPE_CHECKING:
    from test_fixture_types import RunCli, WriteTree

UNCLOSED = {LIBRARY: "crate/unclosed.rs"}


class TestTheCommandAsAStep:
    def test_a_clean_crate_succeeds(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(CLEAN_CRATE)
        assert run_cli_subprocess(FULL_RUN)[0] == 0

    def test_a_crate_with_findings_fails(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(CRATE)
        assert run_cli_subprocess(FULL_RUN)[0] == 1

    def test_prints_every_finding(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(CRATE)
        assert run_cli_subprocess(FULL_RUN)[1].splitlines() == CRATE_FINDINGS

    def test_warn_only_succeeds(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(CRATE)
        assert run_cli_subprocess([*FULL_RUN, "--warn-only"])[0] == 0

    def test_a_file_that_will_not_parse_is_an_error(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(UNCLOSED)
        assert run_cli_subprocess(["src"])[0] == 2

    def test_a_missing_path_is_an_error(self, run_cli_subprocess: RunCli) -> None:
        assert run_cli_subprocess(["/nonexistent/lib.rs"])[0] == 2

    def test_python_dash_m_reads_the_crate(self, write_tree: WriteTree) -> None:
        write_tree(CRATE)
        result = subprocess.run(
            [sys.executable, "-m", "assert_one_assert_per_test", *FULL_RUN],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.splitlines() == CRATE_FINDINGS
