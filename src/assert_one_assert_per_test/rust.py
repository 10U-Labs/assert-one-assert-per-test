from __future__ import annotations

from typing import TYPE_CHECKING

import tree_sitter_rust
from tree_sitter import Language, Parser

from .finding import Finding, Unparsable

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tree_sitter import Node

RUST = Language(tree_sitter_rust.language())

TEST_ATTRIBUTES = frozenset({"test", "rstest", "test_case"})
PANIC_ATTRIBUTE = "should_panic"
ASSERTION_FAMILIES = ("assert", "debug_assert")
COMMENTS = frozenset({"line_comment", "block_comment"})
NESTED_ITEMS = frozenset(
    {"function_item", "impl_item", "mod_item", "trait_item"}
)


def text(node: Node) -> str:
    return (node.text or b"").decode("utf-8", "replace")


def last_segment(path: Node) -> str:
    name = path.child_by_field_name("name")
    return text(path if name is None else name)


def attribute_names(function: Node) -> list[str]:
    names: list[str] = []
    sibling = function.prev_named_sibling
    while sibling is not None and (
        sibling.type == "attribute_item" or sibling.type in COMMENTS
    ):
        if sibling.type == "attribute_item":
            attribute = sibling.named_children[0]
            names.append(last_segment(attribute.named_children[0]))
        sibling = sibling.prev_named_sibling
    return names


def is_test_function(function: Node) -> bool:
    return any(name in TEST_ATTRIBUTES for name in attribute_names(function))


def is_assertion_macro(name: str) -> bool:
    return any(
        name == family or name.startswith(f"{family}_")
        for family in ASSERTION_FAMILIES
    )


def macro_name(macro: Node) -> str:
    path = macro.child_by_field_name("macro")
    return "" if path is None else last_segment(path)


def assertion_macros(node: Node) -> Iterator[Node]:
    for child in node.named_children:
        if child.type in NESTED_ITEMS:
            continue
        if child.type == "macro_invocation" and is_assertion_macro(
            macro_name(child)
        ):
            yield child
        yield from assertion_macros(child)


def is_operand(token: Node | None) -> bool:
    return token is not None and (token.is_named or token.type == "?")


def claim_operators(macro: Node) -> list[str]:
    operators: list[str] = []
    previous: Node | None = None
    for token in macro.named_children[-1].children[1:-1]:
        if token.type == ",":
            break
        if token.type in ("&&", "||") and is_operand(previous):
            operators.append(token.type)
        previous = token
    return operators


def conjunct_count(macro: Node) -> int:
    if macro_name(macro) not in ASSERTION_FAMILIES:
        return 0
    operators = claim_operators(macro)
    if "||" in operators or "&&" not in operators:
        return 0
    return operators.count("&&") + 1


def test_functions(node: Node) -> Iterator[Node]:
    for child in node.named_children:
        if child.type == "function_item" and is_test_function(child):
            yield child
        yield from test_functions(child)


def first_fault(node: Node) -> Node:
    if node.is_error or node.is_missing:
        return node
    return first_fault(next(child for child in node.children if child.has_error))


def check_function(path: str, function: Node) -> list[Finding]:
    name = text(function.child_by_field_name("name") or function)
    body = function.child_by_field_name("body")
    macros = [] if body is None else list(assertion_macros(body))
    panics = attribute_names(function).count(PANIC_ATTRIBUTE)
    count = len(macros) + panics
    findings = []
    if count != 1:
        findings.append(Finding(path, function.start_point.row + 1, name, count))
    for macro in macros:
        conjuncts = conjunct_count(macro)
        if conjuncts:
            findings.append(
                Finding(path, macro.start_point.row + 1, name, conjuncts, True)
            )
    return findings


def scan(path: str, source: bytes) -> list[Finding]:
    root = Parser(RUST).parse(source).root_node
    if root.has_error:
        raise Unparsable(first_fault(root).start_point.row + 1)
    return [
        finding
        for function in test_functions(root)
        for finding in check_function(path, function)
    ]
