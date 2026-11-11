---
name: anything-importable-lives-outside-conftest
description: conftest.py holds only fixtures and hooks; code two tiers share by import is lib/test_read_sample, lib/test_trees and lib/test_fixture_types, reached through PYTHONPATH=lib
metadata:
  type: feedback
---

# Anything importable lives outside conftest

`conftest.py` holds fixtures and hooks, which pytest finds by itself; a test
module never imports from it. What two tiers share by import is a package under
`lib/`, because `lib/` is where code used more than once in this repository
goes: `test_read_sample` reads one sample, `test_trees` holds the crate trees
the CLI is run over, their paths, the findings the findings tree produces and
the `FULL_RUN` arguments that name them, and `test_fixture_types` holds the
`RunCli` and `WriteTree` aliases the fixtures are annotated with.

They are separate because a file reader, a fixture tree and a type alias change
for different reasons. The packages are not named after the tool: what belongs
there is whatever more than one caller needs and no fixture should hold. The
tests themselves do not move there: nothing imports a test, so `test/unit/`,
`test/integration/` and `test/e2e/` stay where they are.

**Why:** importing a conftest instead works only while a package layout keeps
its module name unique, and binds the suite to that layout for a reason nothing
states. A block repeated across tiers also fails `jscpd-test`, which runs at a
threshold of zero.

**How to apply:** every job reaches the modules through `PYTHONPATH=lib` (or
`MYPYPATH=lib`), since `test/` carries no `__init__.py` and pytest puts only a
test's own directory on the path.
