# v3 changes (one row per finding of review-repin2.md)

Not verified on real take files (none present). Every "checked by" below is a run on a made-up folder; raw output is in `evidence-repin3/`.

| Finding | Fix in v3 | Checked by |
|---|---|---|
| 1-6 (majors: masking gaps, false hides, raw files left, e-mail, Q23 coverage, Q27 model side) | One masking choke point (`mask`, plus `mask_line` over the whole output); word-boundary and name-word rules; e-mail masked; canary self-test runs first and aborts with exit 3; work folder holds only masked or name-only files; canary files deleted at once; Q23-1 searches the four files, other code, flows, and prints left-out counts; Q23-2 prints line numbers; qs_37 searched with file counts; spend warning in the doc | `raw-2-selftest-bash.txt`, `raw-2-selftest-dash.txt` (119 cases pass), `raw-3-selftest-AGAINST-V2.txt` (v2 filter fails 43 of them), `raw-canary-fail.*`, `raw-badsed.*`, `raw-run-*.stdout` |
| 7-12 (minors, nits) | Doc rewritten: each code and term explained; two-review disagreement on the delete path stated; Q25 reading and "G1 stays NO" default labelled as builder additions; v5 and v21 names | read of `LEAD-REPIN-VERIFY.md` |

Detail on false hides: `if token:`, `author:`, desk-/task-/risk- names now stay readable (self-test cases added).
Fake secrets in all output and work folders: 0 (dummy run, bash and dash identical; before/after listing identical).
Banned-string count over new files: 0.
Not tested: git branch (brief says no git), WSL, macOS, busybox, the unreadable-file branch as a non-root user.
