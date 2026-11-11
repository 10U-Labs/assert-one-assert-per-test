from __future__ import annotations

from pathlib import Path

import pytest
from test_read_sample import read_sample

from assert_one_assert_per_test.finding import Finding, Unparsable
from assert_one_assert_per_test.rust import is_assertion_macro, scan

PATH = "src/lib.rs"

ONE_ASSERTION = (
    "one_assert",
    "assert_eq",
    "assert_ne",
    "debug_assert",
    "debug_assert_eq",
    "scoped_assert",
    "assert_matches",
    "assert_in_expression",
    "assert_in_closure",
    "assert_in_loop",
    "should_panic",
    "should_panic_with_expected",
    "empty_assert",
)

NOT_TESTS = (
    "not_a_test",
    "cfg_test_is_not_a_test",
    "attribute_on_previous_item",
)

NESTED_ITEMS = (
    "nested_function",
    "nested_impl",
    "nested_module",
    "nested_trait",
)

TESTS_WITHOUT_ASSERTIONS = {
    "no_assert": 2,
    "tokio_test": 2,
    "tokio_test_with_arguments": 2,
    "rstest": 2,
    "test_case": 2,
    "comment_between_attribute_and_function": 3,
    "test_after_other_attribute": 3,
    "test_in_module": 4,
    "other_macro": 2,
    "assert_like_name": 2,
}

CONJUNCTIONS = {
    "conjunction": (4, 2),
    "conjunction_of_three": (3, 3),
    "debug_assert_conjunction": (3, 2),
    "scoped_conjunction": (3, 2),
    "conjunction_after_try": (3, 2),
    "conjunction_with_message": (3, 2),
}

NOT_CONJUNCTIONS = (
    "disjunction",
    "conjunction_under_disjunction",
    "negated_conjunction",
    "conjunction_in_closure",
    "conjunction_in_message",
    "conjunction_in_string",
    "conjunction_in_assert_eq",
    "double_reference",
    "closure_without_parameters",
)

ASSERTION_MACROS = (
    "assert",
    "assert_eq",
    "assert_ne",
    "assert_matches",
    "assert_snapshot",
    "debug_assert",
    "debug_assert_eq",
    "debug_assert_ne",
)

OTHER_MACROS = ("asserting", "assertion", "println", "prop_assert", "debug")


def findings(name: str) -> list[Finding]:
    source = read_sample(Path(__file__).parent, f"rust/{name}.rs")
    return scan(PATH, source.encode("utf-8"))


class TestASampleWithoutFindings:
    @pytest.mark.parametrize("name", ONE_ASSERTION)
    def test_a_test_with_one_assertion(self, name: str) -> None:
        assert not findings(name)

    @pytest.mark.parametrize("name", NOT_TESTS)
    def test_a_function_that_is_not_a_test(self, name: str) -> None:
        assert not findings(name)

    @pytest.mark.parametrize("name", NESTED_ITEMS)
    def test_an_assertion_in_a_nested_item(self, name: str) -> None:
        assert not findings(name)

    @pytest.mark.parametrize("name", NOT_CONJUNCTIONS)
    def test_an_expression_that_is_not_a_conjunction(self, name: str) -> None:
        assert not findings(name)


class TestACountFinding:
    @pytest.mark.parametrize("name", sorted(TESTS_WITHOUT_ASSERTIONS))
    def test_reports_a_test_without_assertions(self, name: str) -> None:
        line = TESTS_WITHOUT_ASSERTIONS[name]
        assert findings(name) == [Finding(PATH, line, name, 0)]

    def test_reports_the_count(self) -> None:
        assert findings("two_asserts") == [Finding(PATH, 2, "two_asserts", 2)]

    def test_counts_should_panic_with_the_assertions(self) -> None:
        assert findings("should_panic_plus_assert") == [
            Finding(PATH, 3, "should_panic_plus_assert", 2)
        ]


class TestAConjunction:
    @pytest.mark.parametrize("name", sorted(CONJUNCTIONS))
    def test_is_reported_on_the_assertion_line(self, name: str) -> None:
        line, conjuncts = CONJUNCTIONS[name]
        assert findings(name) == [Finding(PATH, line, name, conjuncts, True)]

    def test_is_reported_alongside_the_assertion_count(self) -> None:
        assert findings("conjunction_plus_assert") == [
            Finding(PATH, 2, "conjunction_plus_assert", 2),
            Finding(PATH, 3, "conjunction_plus_assert", 2, True),
        ]


class TestAFileThatWillNotParse:
    def test_raises_unparsable(self) -> None:
        with pytest.raises(Unparsable):
            findings("unclosed_parameters")

    def test_names_the_line_of_an_error_node(self) -> None:
        with pytest.raises(Unparsable, match="^line 1$"):
            findings("unclosed_parameters")

    def test_names_the_line_of_a_missing_node(self) -> None:
        with pytest.raises(Unparsable, match="^line 3$"):
            findings("missing_semicolon")


class TestIsAssertionMacro:
    @pytest.mark.parametrize("name", ASSERTION_MACROS)
    def test_accepts_an_assertion_family(self, name: str) -> None:
        assert is_assertion_macro(name) is True

    @pytest.mark.parametrize("name", OTHER_MACROS)
    def test_rejects_other_macros(self, name: str) -> None:
        assert is_assertion_macro(name) is False
