# PR89 round 6 review (redaction path) - head f4301d5, reviewer egm-codebase-details (read-only, snapshot)

Verdict: 0 Blockers, 1 Major, 5 Minors, 2 Nits. Reviewer could not run code or recompute any sha256; did not check Windows or macOS.

MAJOR 1. tests/test_mutation_runner_keywords.py:1473-1483 `test_a_lock_file_with_a_wider_mode_is_refused` chmods the file 0400 and asserts it is accepted, but tools/mutation_runner.py:483-485 opens it O_RDWR, so a non-root owner gets EACCES and the test fails; it passes only as root. The evidence ran as root (r5-old.log paths /tmp/claude-0/). The "another user" test is skipped on non-root runs, and mutant tests/mutation_runner_mutants.py:402 is killed only as root. So "90 passed" and "145/145" hold only as root, not on the CI user. Fix: open read-only for the check or drop the 0400 assertion; make the other-user test and its mutant work without root.

Minor A: lock-file refusal text misleading (:468-470, :493): "delete it by hand" for a file in a sticky folder that cannot be deleted; EACCES/EISDIR/ENOTDIR blamed on another user; st_nlink not checked.
Minor B: m1 only partly closed. Quote-escaped variants built from the str-repr form only; unicode_escape, JSON and bytes-repr forms have none. Leak: password with a non-ASCII letter and a quote (e.g. e-acute + single quote + x) printed through ascii() or bytes repr inside a larger bytes object holding a double quote. Fix: apply the swap to every form; add ascii() and bytes-in-larger-bytes cases to the property test.
Minor C: docs overclaim ("each ... quote mark escaped or not" for all forms; "a hostile line cannot slow the run" is observed only with two timing tests).
Minor D: an unquoted password containing a quote, `;` or `&` printed alone still leaks past the first such character (documented, but fix-dont-defer: add a candidate up to the next whitespace); `\\.` has no DOTALL so a backslash-newline in a quoted libpq password defeats the match.
Minor E: re-encoded copies (repr of a JSON string, doubled backslashes) leak; not named in the docs.
Nit 1: `took < 5` timing bounds may flake. Nit 2: evidence hash cross-checks fine; tests, not the hash, show behaviour.

Round-5 items m2, m3, m5 (code), m6 (form), nits: fixed. MAX_FRAGMENT/MAX_MATCHES: neither leaks nor loses the verdict (judge uses the unmasked first line).
Evidence note: the independent runner at f4301d5 was stopped (head will change); its partial folder was deleted.
