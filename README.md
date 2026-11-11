# assert-one-assert-per-test

Assert that each test function contains exactly one assertion, in any language
the tool can read. Rust is the first.

It is the language-independent sibling of
[assert-one-assert-per-pytest](https://github.com/10U-Labs/assert-one-assert-per-pytest),
and reports the same findings in the same format.

## Why One Assert Per Test?

The "one assert per test" pattern encourages writing focused, atomic tests that
verify a single behavior. Benefits include:

- **Clear failure messages**: When a test fails, you know exactly what behavior broke
- **Better test names**: Tests naturally describe specific behaviors
- **Easier maintenance**: Changes to one behavior don't affect unrelated assertions
- **Faster debugging**: No need to hunt through multiple assertions

## Installation

```bash
pip install assert-one-assert-per-test
```

## Usage

### Command Line

```bash
# Scan a crate's sources and integration tests
assert-one-assert-per-test src tests

# Scan specific files
assert-one-assert-per-test src/lib.rs tests/cli.rs

# Use glob patterns
assert-one-assert-per-test "crates/**/*.rs"

# Exclude patterns
assert-one-assert-per-test . --exclude "*/target/*"

# Verbose output
assert-one-assert-per-test src --verbose

# Fail fast (exit on first finding)
assert-one-assert-per-test src --fail-fast

# Warn only (always exit 0)
assert-one-assert-per-test src --warn-only
```

A directory is read recursively for files in a supported language, skipping
hidden directories. A file in a language the tool cannot read is passed over.

### GitHub Actions

```yaml
- uses: 10U-Labs/assert-one-assert-per-test@v1
  with:
    files: "src tests"
    exclude: "*/target/*"
    verbose: "true"
```

### As a Python Module

```bash
python -m assert_one_assert_per_test src tests
```

## Supported Languages

| Language | Suffixes | Parser                                                              |
| -------- | -------- | ------------------------------------------------------------------- |
| Rust     | `.rs`    | [tree-sitter-rust](https://github.com/tree-sitter/tree-sitter-rust) |

Each language is read by its own grammar rather than by matching text, so an
`assert!` inside a string or a comment is never counted.

## Output Format

Default output shows one finding per line:

```text
src/lib.rs:10:adds:0
src/lib.rs:15:adds_twice:2
src/lib.rs:22:adds_both:2:conjunction
```

Format: `file_path:line_number:function_name:assert_count`

The line number is the line the function's `fn` keyword is on, after any
attributes. A conjunction finding adds a fifth field, `conjunction`. Its line
number is the assertion rather than the enclosing function, and its count is the
number of conjuncts the expression joins.

## Exit Codes

- `0`: No findings (or `--warn-only` specified)
- `1`: Findings detected
- `2`: Error (missing files, unreadable files, syntax errors)

## Rust

### What Counts as a Test?

A function carrying an attribute whose last path segment is `test`, `rstest` or
`test_case`. That covers `#[test]`, `#[tokio::test]`, `#[async_std::test]`,
`#[sqlx::test]`, `#[rstest]` and `#[test_case(...)]`, wherever the function is,
including inside `#[cfg(test)] mod tests`. `#[cfg(test)]` on its own does not
make a function a test.

### What Counts as an Assertion?

- A macro whose last path segment is `assert` or `debug_assert`, or starts with
  `assert_` or `debug_assert_`: `assert!`, `assert_eq!`, `assert_ne!`,
  `debug_assert!`, `debug_assert_eq!`, `debug_assert_ne!`,
  `pretty_assertions::assert_eq!`, `assert_matches!`, and the `assert_*_snapshot!`
  macros from `insta`.
- A `#[should_panic]` attribute on the test, which asserts that the body panics.

An assertion inside a closure or a loop in the test body is counted once, where
it is written. An assertion inside an item nested in the test, a `fn`, `impl`,
`trait` or `mod`, is not counted, since nothing says the test runs it. Neither
is an assertion in a helper function the test calls.

### Conjunctions

An `assert!` or `debug_assert!` whose condition is a top-level `&&` carries one
claim per conjunct, so a red run names the whole expression rather than the
claim that broke. The tool reports it the way it reports a second assertion.

```rust
#[test]
fn parses() {
    assert!(config.name == "app" && config.port == 8080);
}
```

Only a top-level `&&` is refused. These are all allowed:

- `assert!(a || b)`, one claim about two alternatives.
- `assert!(a || b && c)`, where `&&` binds tighter and the claim being made is
  the disjunction.
- `assert!(!(a && b))`, which is `!a || !b`, and so a disjunction.
- `assert!(items.iter().all(|i| i.a && i.b))`, where the `&&` is evaluated per
  item inside a closure rather than joining two claims about the test.
- `assert!(a, "{}", b && c)` and `assert!(a, "b && c")`, where the `&&` is in
  the message.
- `assert_eq!(a && b, true)`, which claims one equality.

### Syntax Errors

A file tree-sitter cannot parse completely is reported as a syntax error naming
the first line it could not place, and the run exits 2, because a test the
grammar misread could be counted wrongly.

## Options

| Option               | Description                                |
| -------------------- | ------------------------------------------ |
| `--exclude PATTERNS` | Glob patterns to exclude (comma-separated) |
| `--quiet`            | Suppress all output (exit code only)       |
| `--count`            | Print only the number of findings          |
| `--verbose`          | Show detailed processing information       |
| `--fail-fast`        | Exit after the first file with a finding   |
| `--warn-only`        | Always exit 0, even with findings          |

## License

Apache 2.0 - See [LICENSE.txt](LICENSE.txt)
