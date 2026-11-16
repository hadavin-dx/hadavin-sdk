# R7T-RESULTS (r7t builder; orders C-R7T, C-R7T-ADD, the lead's flake order, the mail/create_open follow-ups)

Times in UTC. Made-up data only, loopback only, no spend, no live service. Nothing committed or pushed.

## 1. FIRST: what failed, what is uncertain, what I did not check

1. **A real race was found and fixed (it was not a flake).** The r7s test `test_s3_a_created_contact_the_list_does_not_show_ends_the_check_with_the_failed_exit_code[with-cleanup-f3-silent]` failed 1 time in my first staged guard run. Cause, in code:
   - r7s `src/lead_desk/crm_hubspot.py` line 381 (`put`): `self._count("created")` ran only AFTER HubSpot's 201 reply. The attempt counter `creates` is written BEFORE the request (`_call`), `created` after the reply.
   - The crash drill (`scripts/run_real_check.py` lines 907 and 911: `proc.terminate()`, then `proc.kill()` after the wait) stops the first desk while its second batch is in flight. A stop between the request and the count leaves a contact in HubSpot that no counter shows. The restarted desk gets a 409 for that lead, so it counts `conflicts`, not `created`.
   - Raw evidence of the window (r7s sources, `flake-r7s-load-7.log`): `"created": 8, "creates": 10, "conflicts": 1` for 9 leads. The check sums `created` (8) and compares with the contacts the list showed (8 of 9, one hidden by list lag): `max(0, 8 - 8) = 0`, the message "1 contacts may be left" never came and, with floor F3 silent, the exit code would be 0 with a contact left in HubSpot. The test is the right test; the code under it undercounted.
   - Rate on the r7s sources: 1 failure in 30 runs of the series on the r7s sources (run 7), plus 1 in an earlier partial series of about 28 (the same failure; raw log `flake-r7s-load-7.log`).
   - Rate on the fixed r7t bytes: 0 in 30 on the final r7t bytes, plus 0 in the 8 runs of the earlier series on older r7t bytes. Not proof by itself; see the deterministic tests in section 3.
   - Load used: 4-5 other heavy jobs at once (pytest guard run, mutant runs, the other series); never run with an idle machine.
2. **Fix (fail closed, in code).**
   - `crm_hubspot.py`: a create writes `create_open` +1 in the SAME write as its call counter BEFORE the request leaves (`_call`, line 392, `write_stats_strict`: a failed write raises `CrmCounterUnwritable` and the create is NOT sent; `run_stats.write_stats_strict` is new, `write_stats` stays best-effort for every other counter). The outcome and the end of the open create are ONE write (`_settle_create`, line 286): `created`, `conflicts`, `create_unknown` or none.
   - Outcome rules (the lead's gap 1): only a reply that proves nothing was stored (`CrmNothingStored`: a clear 4xx, 429 after the waits, a raise before the request) settles as none. A timeout, a transport error, a 5xx, 408 or an unclear 2xx after the request left settles as `create_unknown` (the contact may exist). A stop that runs no code leaves `create_open` at 1.
   - `run_real_check.py` `contacts_not_accounted_for(created, accounted, open_creates, leads)` (line 605): possible = `created + create_open + create_unknown`, never more than the leads in the book (a lead makes at most one contact), answer = possible minus what the list showed. This is exact in the three real cases: the open create made the contact and it is listed (no false alarm), the open create was retried by the next desk (10 possible, 9 leads, no false alarm), a contact is hidden (reported, exit failed).
   - Atomicity (gap b): `write_stats_strict` writes `<file>.tmp` then `os.replace` (`run_stats.py` lines 16-25); a stop leaves the old whole file or the new whole file. A file missing (desk stopped before it ever wrote) or unreadable makes the counter not known: `counter_is_known` False, the run ends EXIT_FAILED (t9, t2: confirmed by tests below). Also: a desk that was killed before its first write made no create (the open write comes before the request), so a missing file of such a desk hides nothing.
3. **Mail, the same class (the lead's question a).** `smtp_provider.send` writes `attempts` before the connection and `sent` after the dialogue (`smtp_provider.py` lines 272 and 283-284), so `sent` can be one low after a stop. The existing control: floor F4 takes the LARGER of the desk's `sent` and the mails the mailbox reader counted (`run_real_check.py` floor_checks: `sent_total = max(desk_sent, mails)`) and fails when the counter is missing. Deterministic test t16 (pin, passes on r7s too): book of 9 sent, desk says 9, mailbox shows 10 -> F4 fails; mailbox agrees -> F4 holds; no counter -> F4 fails. Residual, stated plainly: a mail that was SENT, not counted and not yet visible in the mailbox (mailbox lag) is invisible to both counters; the checks name that already as the mailbox-lag limit (F4 detail text). It needs a third party (the mail server) to close; next step: none in code.
4. **Not run / not verified.** The take tree on the laptop is unreachable: the lead runs the take-side banner test q1 and `test_take_imports.py` there. Not tried on a real Windows machine. The banner figures 0.0814 and 0.0832 could not be reproduced (section 7). The full suite was NOT run (EV7T does). The `flake30.sh` series was run under load only (section 3). The mutant U6 is equivalent (section 4). Mailbox lag (section 1, item 3) is a third-party limit.
5. EV3: the frozen head is 58aa4031e911e682ec5702e0641d11cbaf927817 (tag `frozen2` in `demo-frozen/repo2`). 49d3c85938fe5323a3378a49195d3b8da434b3ca is the hash of that commit's TREE (`git rev-parse frozen2^{tree}`), measured, not a second head.

## 2. Before / after table (every r7t test against a plain copy of the r7s sources)

Plain copy of tree-R7S plus only `tests/test_r7t_findings.py`; log `before-final-r7s.log`. Result: **138 cases, 78 fail, 60 pass (pins)**.

| group | cases | fail on r7s | pass on r7s (pin) |
|---|---|---|---|
| t1 | 1 | 1 | 0 |
| t2 | 12 | 11 | 1 |
| t3 | 1 | 0 | 1 |
| t4 | 8 | 0 | 8 |
| t5 | 7 | 0 | 7 |
| t6 | 44 | 15 | 29 |
| t6b | 3 | 1 | 2 |
| t6c | 4 | 4 | 0 |
| t7 | 3 | 3 | 0 |
| t8 | 2 | 2 | 0 |
| t8b | 1 | 1 | 0 |
| t9 | 4 | 3 | 1 |
| t10 | 2 | 0 | 2 |
| t11 | 1 | 0 | 1 |
| t12 | 21 | 21 | 0 |
| t13 | 3 | 0 | 3 |
| t14 | 4 | 0 | 4 |
| t15 | 8 | 8 | 0 |
| t16 | 1 | 0 | 1 |
| t17 | 7 | 7 | 0 |
| t18 | 1 | 1 | 0 |
| total | 138 | 78 | 60 |

Pins (pass on both, on purpose): t3 (R27), t4 (R39), t5 (R07) kill named mutants of code that was already right; t6 entry-point cases for the code that already refused (29 cases), t6b bind-call and base-class sweeps, t10 (the counter write was already atomic), t11, t13 (the banner figure was already right), t14 (the guard is new but nothing was skipping), t16 (mail control), t2 first test (R19/R20 reader glob, already right). Each pin exists because a mutant of that line survived EV7S or because the lead asked for the statement.

## 3. The 30-run series (flake30.sh)

| sources | runs | failed | load |
|---|---|---|---|
| r7s (`old/tree`) | 30 | 1 (run 7: created 8, creates 10, conflicts 1 for 9 leads) | 4-5 other heavy jobs (guard, mutants, series) at once |
| fixed r7t bytes (`flT2`) | 30 | 0 | same |

Test: `test_s3_..._with-cleanup-f3-silent` (the `-k s3` series, `flake30.sh`; raw logs `flake-<tag>-<i>.log`, sums `flake-r7s-load.sum`, `flake-r7t-load.sum`). Earlier partial series on older bytes: `flake-r7t-load-oldbytes.sum`. **No run was made with no other load**: the machine was never idle during the box. 1 of 30 is 3.3 percent on r7s; 0 of 30 on r7t does not prove the rate is zero (with 3.3 percent a clean 30 happens about 36 percent of the time), so the proof is the deterministic hook tests t15/t17 (below), not the series.

**The hook tests (the lead's order).** Every t15 test forces the window by a hook: `_Killed(BaseException)` raised at the exact point (nothing after it runs, like a kill), or the wait function replaced by a recorder (the 429 tests), or `read_counter_files_checked` wrapped; no `sleep`, no real kill, no real timing (the 429 tests used a real 0.01 s wait in the first draft; I replaced it by a recorder in this pass: `grep -n sleep|terminate|kill tests/test_r7t_findings.py` finds only comments and the recorder). All 16 cases of t15, t17, t18 FAIL on the r7s sources (log `before-t15-t17-t18-on-r7s.log`: 16 failed, 122 deselected) and PASS on r7t (full file 138 passed, `r7t-file-final.log`). None of them is a pin. Test ids that fail on r7s:

- test_t15_the_counting_rule_takes_open_creates_as_possible_contacts_and_never_more_than_the_leads
- test_t15_the_window_after_the_request_and_before_the_count_leaves_the_create_open
- test_t15_the_window_before_the_reply_also_leaves_the_create_open
- test_t15_every_normal_end_of_a_create_closes_it
- test_t15_a_run_with_a_window_in_the_counter_and_a_hidden_contact_ends_as_failed
- test_t15_a_window_in_the_counter_with_nothing_hidden_is_no_false_alarm[made-and-listed]
- test_t15_a_window_in_the_counter_with_nothing_hidden_is_no_false_alarm[retried]
- test_t15_a_create_that_waits_on_a_429_and_then_succeeds_opens_and_closes_exactly_once
- test_t17_a_create_that_may_have_made_the_contact_is_counted_as_unknown[drop]
- test_t17_a_create_that_may_have_made_the_contact_is_counted_as_unknown[500]
- test_t17_a_create_that_may_have_made_the_contact_is_counted_as_unknown[408]
- test_t17_a_429_after_the_waits_proves_nothing_was_stored
- test_t17_an_unknown_create_with_nothing_hidden_is_no_false_alarm[made-and-listed]
- test_t17_an_unknown_create_with_nothing_hidden_is_no_false_alarm[retried]
- test_t17_an_unknown_create_and_a_contact_the_list_does_not_show_ends_as_failed
- test_t18_a_counters_file_that_cannot_be_written_stops_the_create_before_it_is_sent

t9 (missing counter file, hidden counter) and t10 (the write is atomic) cover the file side: t9 fails closed when a killed desk left no file (confirmed: the counter is then not known, EXIT_FAILED); t10 is a pin (the write was already temp file + `os.replace`).

## 4. Mutants (every row restored byte for byte; raw rows in `snapshot-r7t/mut-results.tsv`)

| id | file | tests | result |
|---|---|---|---|
| R07 | demo_only/bad_request.py | t5 | KILLED |
| R10n | scripts/run_real_check.py | t1 | KILLED |
| R10b | scripts/run_real_check.py | t1 | KILLED |
| R19 | scripts/run_real_check.py | t2 | KILLED |
| R20 | scripts/run_real_check.py | t2 | KILLED |
| R27 | scripts/run_real_check.py | t3 | KILLED |
| R39 | tests/support.py | t4 | KILLED |
| N01 | scripts/run_real_check.py | t2 | KILLED |
| N02 | scripts/run_real_check.py | t2 | KILLED |
| N03 | scripts/run_real_check.py | t2 | KILLED |
| N04 | scripts/run_real_check.py | s3e or t9 | KILLED |
| N05 | scripts/run_real_check.py | t9 | KILLED |
| N06 | scripts/run_real_check.py | t2 | KILLED |
| N07 | scripts/run_real_check.py | t2 | KILLED |
| N08 | scripts/run_real_check.py | t7 | KILLED |
| N09 | scripts/run_real_check.py | t7 | KILLED |
| N10 | demo_only/bad_request.py | t6c or t12 | KILLED |
| N11 | demo_only/fakes_server.py | t6 | KILLED |
| N12 | demo_only/fake_imap.py | t6 | KILLED |
| N13 | demo_only/fake_smtp_tls.py | t6 | KILLED |
| N14 | scripts/run_real_check.py | t8 | KILLED |
| N16 | scripts/run_real_check.py | t9 | KILLED |
| M1 | scripts/run_real_check.py | t15 | KILLED |
| M2 | scripts/run_real_check.py | t15 | KILLED |
| M3 | scripts/run_real_check.py | t15 | KILLED |
| M4 | scripts/run_real_check.py | t15 | KILLED |
| M5 | scripts/run_real_check.py | t15 | KILLED |
| M6 | scripts/run_real_check.py | t15 | KILLED |
| C1 | src/lead_desk/crm_hubspot.py | t15 | KILLED |
| C4 | src/lead_desk/crm_hubspot.py | t15 | KILLED |
| C5 | src/lead_desk/crm_hubspot.py | t15 | KILLED |
| C6 | src/lead_desk/crm_hubspot.py | t15 | KILLED |
| U1 | scripts/run_real_check.py | t17 | KILLED |
| U2 | src/lead_desk/crm_hubspot.py | t17 | KILLED |
| U3 | src/lead_desk/crm_hubspot.py | t17 | KILLED |
| U4 | src/lead_desk/crm_hubspot.py | t17 | KILLED |
| U5 | src/lead_desk/crm_hubspot.py | t18 | KILLED |
| U6 | src/lead_desk/crm_hubspot.py | t18 | SURVIVED |
| U7 | src/lead_desk/crm_hubspot.py | t18 | KILLED |
| C2 | src/lead_desk/crm_hubspot.py | t15 | KILLED |
| C3 | src/lead_desk/crm_hubspot.py | t15 | KILLED |
| C7 | src/lead_desk/crm_hubspot.py | t15 | KILLED |
| N15 | scripts/run_real_check.py | s3 or t9 | KILLED |

43 mutants, all restored byte for byte (`restored-byte-equal=True` 43 times, False 0 times): 42 KILLED, 1 SURVIVED. The survivor is **U6**, an EQUIVALENT mutant: it replaces `raise CrmCounterUnwritable(` by `pass; raise CrmCounterUnwritable(`, which behaves exactly the same; no test can tell them apart. Rows R/N were run on the final bytes; C2, C3, C7 and N15 had stale patterns in the first pass (NOT-APPLIED) and were re-run on fresh copies after I corrected the patterns (rows in `mut-final-C.tsv`, `mut-final-D.tsv`). The mutants were run on the bytes before the last ruff re-format of the test file (whitespace only, no code change).

The five EV7S survivors: R10 (`created or 0`) no longer exists as text: the rule is now `possible = created + max(0, open)` and a `None` counter raises; the variants R10n and R10b of the new text are KILLED by t1. R19, R20 KILLED by t2; R27 by t3; R39 by t4; R07 by t5 alone (the r7s/r7t file).

## 5. Existing tests that I changed (none deleted, none loosened)

| test | old | new | why it is not weaker |
|---|---|---|---|
| `test_r7s_findings.py::test_s3c_the_counting_rule` | `assert rrc.contacts_not_accounted_for(None, 5) == 0  # no counter: check F3 already fails that run` | `for accounted in (0, 5): with pytest.raises(rrc.CounterUnreadable): rrc.contacts_not_accounted_for(None, accounted)` | The old line pinned the fail-OPEN meaning (an unknown counter = nothing missing). F3 never reads the counter, so the old comment was false. All other assertions of the test are kept. |
| `test_r7s_findings.py::test_s3e` (exit codes) | five rows of `(ok, written, left, unseen, zero)` called `exit_code_of(ok, written, left, unseen)` | the same five rows with `known=True` plus one new row `(True, True, [], 0, False, False)`; call `exit_code_of(ok, written, left, unseen, known)` | Every old row is kept with the same expected value; one row is added; the new argument is required. |
| `test_real_check_dry.py` line 308, `test_r7c_one_json_loader.py` line 138 | `rrc.Desk(env, Path("."), 1, "t")` / `Desk({}, Path("."), 1, "x")` | the same call with the fifth argument `"rabcdef"` | `Desk` now requires the run tag (an empty or missing tag wrote files the reader never reads). Same assertions. |

## 6. Findings and siblings (class: an empty or falsy value silently replaced by a default, and the crash window)

Fixed test-first: `make_fakes_server(host="")` and `FakeImap`/`FakeSmtp`/`make_model_server` with any non-loopback host (`require_loopback_host`, one helper; the two mail fakes bound ANY host on r7s: new finding); `port or 8765` (`desk_port`, 0 refused); `dry_smtp_script or "ok"` (`is None`); `Desk(tag=None)`; the counter that fails open (missing, unreadable, empty glob, no `created`); the crash window (section 1). Hosts tested on every entry point: 0.0.0.0, 192.0.2.1, "", "::", example.com, None (default for `make_fakes_server` only), whitespace, LOCALHOST, localhost., [::], 0, 127.1, ::ffff:127.0.0.1, 127.0.0.2, bytes. `is_loopback_host` per spelling: True for localhost in any case, 127.x, ::1, ::ffff:127.x (brackets allowed); False for "", whitespace, "localhost.", "[::]", "::", "0", "127.1", "0x7f.0.0.1" and spellings with a trailing space; TypeError for bytes (caught by `require_loopback_host`, fails closed). A NEW def with a host or bind parameter in `demo_only` fails `t6b` and is named; a new bind call or server base class fails the other two sweeps.
Checked and left: IMAP host blank (already refused at `ImapSettings.__post_init__`), `port(0) or free_port()` (0 means an ephemeral port on purpose), `REAL_IMAP_n_FOLDERS=""` (an empty tuple, not a default replacement; noted), `crm_per_lead.get(lid, 0)`, the R19 statement: R19 is NOT equivalent (a tag that only starts with this tag, or a file with no label, would be read); same-tag `.smtp.json`/`.log` are not read (t2).
R39 consumers: `grep -rn REQUIRE_SCAN tests tools` finds only `tests/support.py` (read with `os.environ.get(...)` truthiness) and tests that set it; t11 fails if any test compares it with `==` or `!=`; t4 pins "true" and every other non-empty value.

## 7. Banner worst-case figures

t13 recomputes the figure from `worst_case_usd` and the request builders for three price/model scenarios by independent arithmetic: it passes. The constants 0.0814 and 0.0832 appear only in the q1 docstring as an r7p example; there is no default price in the code, so they cannot be derived from the repository; a search over plausible parameters found no match. Reported as: not reproducible from the repository, no code claims them.

## 8. Deliverables, hashes, apply matrix

- `core-fix-on-frozen-r7t-crlf.patch` sha256 c39c3680c4ab44c48f0d75f8d99ea29ee5b040b9f5e8333ad0b0349dd2b85843
- `core-fix-on-frozen-r7t-lf.patch` sha256 5a4ad881a8f138768667138eea5af78aea647515a9fe385b0cd03015b0c78299
- `core-fix-r7s-to-r7t-delta.patch` sha256 d67bc302b5dbbb2007ff0dbbc70b96f8c0aa36edeb6d319958d6ac20bc743c20
- `apply-matrix-r7t.txt`, `snapshot-r7t/` (MANIFEST.txt: path + sha256 of every file), `snapshot-r7t/delta-r7s-to-r7t.diff` (12 files), `snapshot-r7t/mut-results.tsv`, `checkpoint.md`.
- Final source sha256: crm_hubspot.py ac0478269b8397c6b000a05c9405f3cf0ff485aa1909e36c6fe9c68997777d2e, run_stats.py 16f5fd67e43ba2311419a23924d1999f8d889a59de3cc3e393392592bc29c342, run_real_check.py bbd3fe16a01c3af9d6bceb0b3eec5c3eee9a9c958a2b553eb437748da7bf60da, tests/test_r7t_findings.py 439f78df28c8e7db5a98538d8ee3d054553a5d8e47ed0e89d88593a717722130 (re-formatted by ruff 15:36 UTC; the guard run below ran on the bytes before that whitespace-only change, then the whole file was run again on the final bytes).

Apply matrix (`apply-matrix-r7t.txt`): a-crlf, b-crlf, c-lf. `git apply --check` and apply rc=0 on fresh plain copies of `demo-frozen/repo2` (`frozen2`); cells a and b equal tree-R7T byte for byte; cell c differs only in the two .ps1 line ends (expected, compared with line endings ignored in the last line of the file). 167 changed files on the frozen tree, 12 in the delta.

## 9. Text for the lead to edit (I cannot edit `handover/`)

- `handover/core/fix/README.md` line 31 and `handover/core/fix/APPLY-README-SNIPPET.md` (r6 text): replace with `README-r7t-SNIPPET.md` (also `snapshot-r7t/APPLY-README-r7t.md`). All its numbers come from `apply-matrix-r7t.txt` and the test runs named here: 167 changed files, `tests/test_reset_scripts.py` 67 passed.
- The false F3 text: it lived in handover `R7S-RESULTS.md` ("no counter: check F3 already fails that run") and in the r7s docstring/test comment; the code docstring and the test are corrected in r7t; the lead replaces the sentence in R7S-RESULTS.md with: "a counter that is not known is not 'nothing missing': F3 never reads the counter, so r7t fails the run."
- `snapshot-r7t/TAKE-USED-FILES-r7t.md` and `test_take_imports.py` replace the r7r/r7s list; run the test on the take tree (the take-side q1 is yours: the take tree is on the laptop, unreachable here). On tree-R7T it gives 392 passed; on the r7s copy 3 failed.

## 10. Guard and changed test files on the final head

- Staged git copy (git init, git add -A, no commit), recipe PLAYWRIGHT_BROWSERS_PATH, GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1: the 22 guard files plus test_r7t_findings, test_real_check_dry, test_r7c_one_json_loader, test_crm_hubspot, test_r7h_findings, test_reset_scripts: **1526 passed, 1 skipped in 1137 s** (`hy-guard-final.log`; the skip is `test_path_confinement.py:285`, `ntpath.isreserved` needs Python 3.13, present before r7t). Bytes: crm_hubspot.py, run_stats.py, run_real_check.py as listed (after the crm_hubspot change), test file before the final ruff whitespace re-format.
- Final bytes of the test file: `tests/test_r7t_findings.py` alone **138 passed in 412 s** (`r7t-file-final.log`).
- Take test: 392 passed on tree-R7T, 3 failed on the r7s copy (`snapshot-r7t/test_take_imports.py`).
- Apply matrix: see section 8.

Suppression count (one grep): 367 (expected 367, delta 0). Ruff 0.17.1 `check` and `format --check` on a copy: check: All checks passed; format --check: 231 files already formatted (after one `ruff format` of the test file).
