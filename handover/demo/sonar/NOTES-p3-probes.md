# P3 single-function probes (sonar-p3-probe-a.patch, sonar-p3-probe-b.patch)

Both change ONLY `load_tools/check_invariants.py` `read_jsonl` (S8707 at L63 on db54e13) plus the three constants it needs (REPO_ROOT, ROOTS_ENV, MAX_PATH_CHARS) and `import tempfile`; each adds one test file (`tests/test_probe_p3a.py`, `tests/test_probe_p3b.py`, 11 test cases). Push ONE of them as a small commit and read the flows of the issue "check_invariants.read_jsonl" with the API call in PROBE-AB-NOTE.md.

## What each does
* A (inline guard in the same function): `real = os.path.realpath(path)`; commonpath against the allowed roots (current folder, repository, temp folder, `LEAD_DESK_PATH_ROOTS`); `raise InputError` when outside or empty/too long/unresolvable; `open(real)`.
* B (flow-breaking): same realpath and roots check, then the file is found by NAME through `os.scandir` listings, one folder level at a time, starting at the allowed root; the opened text is the listing entry's `.path`, never the argument text (the brief's `next(c for c in os.scandir(root) if ...)` form, extended to nested folders so the reader keeps working for any file below a root). Output form for B (match the parent folder, use basename) is NOT in these probes (read_jsonl only reads); it is in the helper of the v2 patch (new name rebuilt from an allowed-character table) and in probe-ab.patch (scrub 179, load_driver 366/377).

## Behaviour and tests (made-up data, a "jail" folder inside tmp)
Inside file relative, nested, name with `?` and `#`, `sub/../a.jsonl` read; `..` and absolute escape, link to a file and to a folder outside, prefix-sibling folder, NUL/newline/empty/5000 chars, missing file, folder given as file, extra root from the environment. Fails before: 4 of 11 fail on db54e13 (escape tests and the NUL case; the rest pass because they describe behaviour the old code already had). After: 11 pass; with test_load_tools and test_hygiene 103 passed, 3 skipped (both probes). Mutants: A without the raise: 3 fail; B without the commonpath check: 4 fail; B opening the argument text instead of the entry: SURVIVES by design (same behaviour; only Sonar's flow differs), as does B joining the argument's own part text. ruff, format, mypy linux/win32 clean. Evidence: evidence-p3v2-1 and -2.

## What counts as SUCCESS from the Sonar API
After pushing, query the PR with `additionalFields=_all`, rules S8707 and S8706:
* SUCCESS: no issue whose component is load_tools/check_invariants.py and whose message ends "in check_invariants.read_jsonl()". All other issues (the other 11) must still be there unchanged; if they changed, the probe affected more than it should.
* PARTIAL (read the flow): the issue is still there but its Sink location moved or its steps changed (for example the Sink now at your `open(real)` or the flow goes through `os.path.realpath`): the engine saw the guard and ignored it; that tells you which call it treats as a propagator.
* FAILURE: the issue is unchanged, same sink line shape and the same steps.
* A new issue on read_jsonl with another rule or line is a failure of the probe (report its text).
Both probes: apply on db54e13 alone, after P1, P1v2 and P2 (measured, evidence-p3v2-2 and -7).
