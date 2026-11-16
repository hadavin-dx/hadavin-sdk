# R7P results (builder; every claim unverified until an evidence runner and a fresh reviewer check it)
Tree: /home/user/build/rr6/tree-R7P (r7o + test changes only; NO source file changed: delta r7o->r7p touches 3 test files). Times UTC.

## What failed, what was NOT run (first)
- Item 1 hygiene run on a staged git copy: **NOT RUN (blocked by a permission denial; the lead decides).** The fix (host built from parts) is in; the proof is missing. A grep for the old literal in tests/ finds none.
- Full suite: not run (by brief). bandit, mypy: not run. Windows: not run. gitleaks: not run.
- Item 8c (skip counts, hygiene 24 vs 20+4): hypothesis, not verified: EV7N's wrapper sets GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1; the builder's recipe did not, so the gitleaks tests skipped. I did not run it.
- Item 9: no reviewer findings reached me.
- Mutant runs used `-k` on the matching tests, not whole files.
- Not done and cannot be: fail-before of the new r7p tests on r7o: they are PINs by design (source was right); each kills a named mutant.

## Items
1. [Major] test_r7o_findings.py: both hubapi hosts now `"https://" + "someuser" + "@" + "api." + "hubapi" + ".com"` (and the `:pw` form). Hygiene run: NOT RUN (see above).
2. [m1] tests/test_r7p_findings.py::test_the_not_utf_8_refusal_hides_the_decode_error_behind_it (b"\xff": read_regular_text, load_json_file, plus siblings iter_regular_lines and read_secret_line): `__suppress_context__ True`, `__cause__ None`, no "codec"/"position" in the traceback. Mutants P01 (read_regular_text) KILLED, P02 (iter_regular_lines:150) KILLED. P03 (`_read_secret_text:97`) SURVIVES and is equivalent: its only caller read_secret_line runs scrub_error; the "secret" case still pins the public behaviour.
3. [m2] test_a_password_without_a_user_name_in_the_hubspot_base_address_is_refused (`https://:pw@api.hubapi.com`, `http://:pw@127.0.0.1:9`, from parts). P04 (drop `or parts.password`) KILLED (2 failed).
4. [EV7N Major] tests/test_r7n_findings.py `_EchoImap` now answers CAPABILITY (`* CAPABILITY IMAP4rev1` + tagged OK) and LOGOUT, counts `logins`; `_run_imap` asserts `logins >= 1` (so the test cannot be vacuous). The two tests where LOGIN never reaches the wire (error in the middle of login, imaplib abort) pass `login_reaches_server=False`.
   - On r7m (copy of tree-R7M + new test file, `-k "n1_a_refused or middle or imaplib"`, 22 tests): 22 FAILED (n4-on-r7m.log); the echoed LOGIN line with the password is in `ImapCountError.__context__`. On r7p: 22 passed (n4-on-r7p.log).
   - Mutants (mut-results.tsv): S01 remove @secret_boundary on imap `_session` KILLED; S02 remove `__context__ = None` KILLED; S05 remove clear_frames KILLED; S03 remove `__cause__ = None` and S04 remove the chain walk SURVIVE the imap tests (the echo arrives as an implicit context, not a cause) and are KILLED by the existing scrub_error unit tests (S03w, S04w); S06 `raise failure` without `from None` SURVIVES, equivalent (raised outside the except block); S09 `ImapConnectionError(str(e))` SURVIVES, equivalent for the echo (logging_in is false on that path). Echo-only mutants S07 (abort path `ImapCountError(str(e))`) and S08 (IMAP4.error path same): KILLED by the new tests, SURVIVE the old tests (r7n as shipped in r7o).
5. [n1] three raw U+FEFF characters in test_r7o_findings.py replaced by the escape `﻿` (assertions unchanged).
6. [n2] `# type: ignore[misc]` removed (mypy files = src, tools, scripts/hubspot_probe.py; tests are not checked, so it did nothing). Counts below.
7. [n3] tests: REAL_DRAIN_SECONDS and REAL_MAIL_WAIT_SECONDS accept 86400 and refuse 86400.5 (P05 high x10 KILLED); a spy on `positive_seconds` pins ("REAL_DRAIN_SECONDS", 150.0) at the call site (P06 default 151.0 KILLED).
8. EV7N observations:
   a. "Exception occurred during processing of request from ('127.0.0.1', N)": printed by socketserver's default `handle_error` in a fake server's handler thread. Cause found: tests/test_fakes_body_before_answer.py (position in the EV7N dot line, about test 995, matches this file in collection order). The fake servers in demo_only (traceback: demo_only/fake_hubspot.py `_send` -> socket write) raise `BrokenPipeError` when they write the reply after the test client has closed the connection on purpose (the tests send a body-less or bad request and hang up). Narrow run on tree-R7N, that file only (ex-suspect.log): 17 passed, 11 such tracebacks, all `BrokenPipeError: [Errno 32] Broken pipe`. In a full run pytest's capture shows only the one that fell outside a test's capture window. It is a server thread's expected error on a vanished client, not a failed test and not a leak into results. The desk's own server (src/lead_desk/server.py handle_error) already silences this class for the real desk; the demo_only fakes do not. NOT changed in r7p (demo_only fakes; a change is outside the items): the lead decides whether to quiet it (same class fix as server.py `_GONE`).
   b/c. skips 8 vs 37 and hygiene 24 vs 20+4: hypothesis, not verified (gitleaks env, see above).
9. none received.

## Changed existing tests (old assertion -> new, why not weaker)
| file / test | old | new | why not weaker |
|---|---|---|---|
| test_r7n_findings.py `_EchoImap` | answered every line except LOGIN with BAD (client aborted before LOGIN) | answers CAPABILITY and LOGOUT, counts LOGINs | the leak assertions are unchanged; a new assertion (`logins >= 1`) is added |
| test_r7n_findings.py `_run_imap` + 2 callers | returned the caught error | same, plus `assert srv.logins >= 1` unless `login_reaches_server=False` (the two tests where LOGIN is never sent) | stronger |
| test_r7o_findings.py o5 params, o4 asserts, `_flaky_crm` | literal host; raw U+FEFF; `# type: ignore[misc]` | built from parts; `﻿` escape; comment removed | same values and assertions |

## Suppressions (grep -o count over *.py,*.toml,*.yml,*.yaml,*.ps1,*.sh, tree minus data and __pycache__; includes occurrences in comments; method differs from EV7N's so numbers are not comparable to its table)
| | r7o | r7p |
|---|---|---|
| noqa | 184 | 188 (+4: the four E402 lines in the new test file, the house style after `sys.path.insert`; test_r7o keeps 8) |
| type: ignore | 127 | 126 (-1) |
| nosemgrep | 31 | 31 |
| nosec | 8 | 8 |
No new type: ignore; the 4 new noqa E402 are the same pattern as in test_r7o_findings.py and test_real_check_dry.py. So "no new suppression" is NOT true: +4 noqa E402.

## Narrow runs
- Final bytes: tests/test_r7p_findings.py + test_r7o_findings.py + test_r7n_findings.py (whole files): **124 passed in 192.93s, rc 0** (final.log), under `unshare -n` with the lo_up driver. Earlier: 25 passed (r7p+r7o, n1.log).
- Ruff 0.17.1 on a plain copy (rc/): `check` "All checks passed!", `format --check` "228 files already formatted". (An earlier copy failed E501 on my first header table; fixed.)

## Deliverables (out/R7P/)
core-fix-on-frozen-r7p-crlf.patch, core-fix-on-frozen-r7p-lf.patch, core-fix-r7o-to-r7p-delta.patch, sha256-r7p.txt, apply-matrix-r7p.txt (a, b CRLF checkouts and c LF checkout: `git apply --check` rc 0 for all three; crlf patch on frozen2 gives tree-R7P byte for byte; delta on r7o gives r7p), build_patches.sh, apply_matrix.sh, mut.py, mut-results.tsv, mutraw-*.txt, runtests.sh, checkpoint.md. Trees: tree-R7P (work), mut-tree (mutants, restored), tm (r7m copy), rc (ruff copy). Nothing committed or pushed in /home/user/hadavin-sdk; no runner left.
