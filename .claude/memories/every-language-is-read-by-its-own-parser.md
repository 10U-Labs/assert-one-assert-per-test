---
name: every-language-is-read-by-its-own-parser
description: A language is read by its own tree-sitter grammar in its own module, never a text match; read before adding a language or reaching for tree-sitter-language-pack
metadata:
  type: project
---

# Every language is read by its own parser

Each language has a module under `src/assert_one_assert_per_test/`, `rust.py`
first, that reads a file with that language's grammar and returns its findings,
and one row per suffix in `SCANNERS` in `scanner.py`. What a test is, what an
assertion is and what a conjunction is are decided on the tree, by node type and
by a node's own text, never by matching characters in the source.

**Why:** a text match counts an `assert!` inside a string, a comment or a doc
test, and cannot tell a binary `&&` from a double reference `&&x` or a closure
`||`, which differ only in what token comes before them. The failure is silent
in the direction that matters: a missed second assertion leaves a job green.
Rust macro arguments are a `token_tree` the grammar does not parse into an
expression, so `claim_operators` reads the tree's direct tokens and decides
binary-ness from the token before each operator. That is still a reading of the
tree, not of the characters: nesting, strings and the message after the first
top-level comma are already separated by the grammar.

**How to apply:** a new language gets its own grammar dependency, its own
module exposing `scan(path, source: bytes) -> list[Finding]`, its suffixes in
`SCANNERS`, its own sample folder in each tier, and its own section in
`README.md` saying what counts as a test, an assertion and a conjunction there.
`tree-sitter-language-pack` is not the shortcut it looks like: it ships hundreds
of grammars to serve a few, and pins them together so none can move alone.

A file the grammar cannot parse completely is `Unparsable`, exit 2, rather than
whatever the grammar recovered. That differs from `assert-no-comments`, which
reports what it can: a misread test here would be counted wrongly, and a wrong
count is a false finding or a missed one.
