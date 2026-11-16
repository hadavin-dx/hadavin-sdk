Start 2026-11-16T14:13:53Z. v4 backed up as *.v4.*

## 14:32 UTC (20:02 IST) checkpoint
Done: v5 script (sed name rule, YAML headers, fail-closed containers, checksum allow-list, PATH/set +x, QUIT trap, kill_tree, run check, inline verdict recount, new tests). --self-test 1011 passed 0 failed (dash and bash). v5 tests against the v4 filter: 388 fail (evidence-repin5/01).
Next: probe set (40+ new lines), mutants, signals via python launcher (INT, QUIT), non-root, timing, then the guide v5, v5-CHANGES.
Blockers: none. Commit SHA: none (no commit allowed).

## 15:06 UTC (20:36 IST) final note
Done: script v5 (self-test 1022 passed 0 failed under dash and bash), 14 mutants x 2 shells all caught (evidence-repin5/04), 49-line probe (2 documented leaks), signals incl. INT and QUIT via python launcher (05), non-root run (06), 1 MB timing (07), hashes and scan (08), guide v5, v5-CHANGES.md. Banned-string scan: 0 hits. No commit made (none allowed).
Not done: nothing on the list; limits are in the guide (busybox, macOS, WSL, real test program untested; bare "passwd NAME" and "-p VALUE" lines stay visible).
