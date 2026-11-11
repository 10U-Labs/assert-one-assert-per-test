from __future__ import annotations

LIBRARY = "src/lib.rs"
TESTS = "tests/cli.rs"
NOTES = "notes.txt"

CLEAN_CRATE = {
    LIBRARY: "crate/clean_lib.rs",
    TESTS: "crate/clean_tests.rs",
    NOTES: "crate/notes.txt",
}

CRATE = {
    **CLEAN_CRATE,
    LIBRARY: "crate/findings_lib.rs",
    TESTS: "crate/findings_tests.rs",
}

CRATE_FINDINGS = [
    f"{LIBRARY}:10:adds:0",
    f"{LIBRARY}:15:adds_twice:2",
    f"{LIBRARY}:22:adds_both:2:conjunction",
    f"{LIBRARY}:28:overflows:2",
    f"{TESTS}:4:adds_from_outside:0",
]

FULL_RUN = ["src", "tests"]
