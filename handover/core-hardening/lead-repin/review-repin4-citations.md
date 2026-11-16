# Citation check of LEAD-REPIN-VERIFY.md (v4) and lead-repin-verify.sh

Checked 2026-11-16 (UTC) by a citation checker. Nothing in the guide was changed. Checked against: `ORDERS.md`, `QUESTIONS.md`, `inputs/*`, `steps-edits/*`, `evidence-repin4/*` (all under `handover/core-hardening/`), and the script itself.

**Count (one per table row): OK 36 / WRONG 4 / UNREADABLE 7.** (The 4 WRONG are listed first. The 7 UNREADABLE are source files that are not in this checkout, so their line numbers cannot be opened.)

Plain note on what "UNREADABLE" means here: the take program (`run_real_check_n8n.py`), the CRM module (`crm_hubspot.py` of the take) and the other take files are not present in this checkout, so any line number inside them cannot be confirmed or refuted. `crm_hubspot.py` copies that exist under `handover/core/` belong to a different package (`lead_desk`) and are not the take's file.

## Failures first

| # | Guide says | Source says | Verdict |
|---|---|---|---|
| 1 | Release note `steps-edits/LEAD-RELEASE-NOTE-v5.md` is "the newest"; owner sheet `OWNER-SHEET-v21.md` (words section, "Release note" and "Owner sheet" entries) | `steps-edits/` now also holds `LEAD-RELEASE-NOTE-v6`, `-v7`, `-v8` (v8 saved 14:09) and `OWNER-SHEET-v22`, `-v23`, `-v24-A`, `-v24-B` (v24-A saved 14:09). v5 and v21 were saved 13:09 and 13:11. Row numbers differ in v8 (for example G16 is at line 61 in v8, line 56 in v5; v8 says "test program" where v5 says "take program"). Every G-number and R-number citation in the guide was checked against v5 / v21 only. | WRONG (stale: the guide cites older versions than the newest on disk; G and R citations not re-checked against v8 / v24-A) |
| 2 | Q27 b outcome: "owner sheet line 44 already carries 'NOT SHOWN'" | `OWNER-SHEET-v21.md` line 44 is the "Set phrases you send" line and has no "NOT SHOWN". The words are on line 52: `Spend lock: shown (or NOT SHOWN)` and `End-date refusal: lead verifies at re-pin (or shown)`. So the End-date refusal line does not carry "NOT SHOWN" at all; only the Spend lock line does. | WRONG (line number and content) |
| 3 | "ORDERS.md lines 185-198, lead answers of 12:50Z" | The 12:50Z answers Q22 to Q31 are lines 185-194. Lines 196-198 are ORDER 039 (12:56Z), a different message; line 199 is the 13:03Z answer. The quoted Q23, Q25 and Q27 texts are correct (lines 187, 189, 191). | WRONG (range too wide by 4 lines; quotes themselves OK) |
| 4 | "A 1 MB single line takes about 0.5 seconds (evidence-repin4/04-timing-1mb.txt)" | The file shows 0.567 s and 0.626 s (980,003 bytes, dash and bash) and 0.612 s and 0.697 s (1,080,003 bytes). Range 0.57 to 0.70 s. (`checkpoint-repin4.md` also says "about 0.5 s".) | WRONG (understated; say about 0.6 to 0.7 seconds) |

## UNREADABLE (source not in this checkout)

| # | Guide cites | Why unreadable |
|---|---|---|
| 5 | `run_real_check_n8n.py` lines 1045-1056 (Q23-2) | file absent |
| 6 | `crm_hubspot.py` lines 500-512 (Q23-2) and 504-509 (AGENT-SCOPE quote) | take's file absent |
| 7 | `run_real_check_n8n.py:1051` (the DELETE call reading) | file absent. ORDERS Q23 itself calls it UNVERIFIED stale text. |
| 8 | `n8n_drive.py`, `n8n.py` named in the hand-typed commands | files absent |
| 9 | Guide statement that the model program folder and the flows folder hold the files the blocks search | not present |
| 10 | `review-codebase-1.md` finding F-01 "CODE-CHANGE-NEEDED" | the review file is not in this checkout (`find` found none). The AGENT-SCOPE text does carry the words `review-codebase-1.md` F-01 and `CODE-CHANGE-NEEDED` (line 20), so the guide quotes AGENT-SCOPE correctly; the review itself cannot be opened. |
| 11 | Unreadable-file branch seen "as an ordinary user (uid 65534) in v2" | v2 evidence (`raw-dummy-run2.txt` line 249) shows an UNREADABLE line and `evidence-repin2*.md` mentions 65534; v4 did not re-run it (the guide says so itself). Counted as UNREADABLE only because the uid is not shown in the raw file I opened; low risk. |

## OK (source opened and agrees)

| # | Guide cites | Source |
|---|---|---|
| 12 | AGENT-SCOPE line 20 says the take archives its contacts as a DELETE at `run_real_check_n8n.py:1051` and `crm_hubspot.py:504-509`, per `review-codebase-1.md` F-01, CODE-CHANGE-NEEDED, not fixed | `inputs/AGENT-SCOPE-DO-AND-DONT.md` line 20 (section 3 "MAY") says exactly this |
| 13 | AGENT-SCOPE line 22 mentions a typed worst-case figure | line 22, "the typed worst-case figure must be a finite positive number" |
| 14 | AGENT-SCOPE line 23, BL-wp6-G1 and the local copy of the flows with real values | line 23 holds "BL-wp6-G1 ... take-time literal substitution into a local copy of the flows" |
| 15 | `~/.hadavin-take-tags/<id>.used` single-use marker (AGENT-SCOPE) | line 20 and 22 |
| 16 | AGENT-SCOPE section 2: the model program holds the real model key | section 2 (line 12) "Identity ... reads the Anthropic key from a key file" |
| 17 | ORDERS Q23 (line 187): decision 2 stays, r17 review 11:00Z found no delete path, only `rows_with_prefix` GET, line 1051 UNVERIFIED stale, key not widened | line 187 |
| 18 | ORDERS Q25 (line 189): cancel-by 18:19 UTC (23:49 IST); Wed 18 Nov; "no take on 23 Nov unless Q27 is shown at the final head" | line 189 |
| 19 | ORDERS Q27 (line 191): UNVERIFIED; lead reads the file at the final head; write "lead verifies at re-pin"; use defaults | line 191 |
| 20 | Q22 (c) in force, "a gap longer than the lease is not claimed" | ORDERS line 186; release note v5 line 118 |
| 21 | Q20.4 and Q21.4 = exit code and retake count | `QUESTIONS.md` line 84 |
| 22 | Q26: none exists; owner cancels the key himself; no "go" on 23 Nov | ORDERS line 190; release note G30 (line 59) |
| 23 | `DECISION-one-store.md` line 14 says ONE database | `inputs/DECISION-one-store.md` line 14 |
| 24 | Release note G1 (re-pin, no delete call, second reader named) | v5 line 21 |
| 25 | G4/G14 call ceiling, ledger, program limit | v5 lines 24, 34 |
| 26 | G6 exit codes, default `none` | v5 line 26 |
| 27 | G7 ports 5678, 5679, 5690-5693, 5701/5702 | v5 line 27 |
| 28 | G10 formula, `need_seconds`, worked example uses 860 seconds | v5 lines 30, 70, 72 |
| 29 | G12 lease sentence | v5 line 32 and 118 |
| 30 | G16 refusal after deadline; G26 checksum again before the run | v5 lines 56, 58 |
| 31 | G17 delete wording; G18 early cancel (sheet 7.7 and 8.1); G20; G21 permissions; G27 clean-up sentence | v5 lines 36, 37, 39, 40, 64 |
| 32 | G33 spend lock/go marker; G34 cancel race and "exit code accepted then: none"; G35 typed figure; G36, G37, G38 | v5 lines 46-51 |
| 33 | Ban list item 10 (take program deletes / does not delete contacts unless G1 and the printed result both show) | v5 line 117 |
| 34 | Owner sheet R3 hard end, R5 compare numbers (a "deleted or archived" line is a difference), R6 typed by hand, R10 FREEZE, R4 and 8.1 spend-lock wording | `OWNER-SHEET-v21.md` lines 32-42 and 36, 111 |
| 35 | Owner sheet 7.7 (an error printed after cancelling: type nothing, report) | line 107 |
| 36 | v2 of the guide named release note v4 and owner sheet v20 | `LEAD-REPIN-VERIFY.v2.md` |
| 37 | Test counts: 288 canary checks, 11 machinery checks, 299 passed 0 failed under dash and bash | `evidence-repin4/03-selftest-dash.txt` and `-bash.txt`: 299 PASS lines each, 11 "(machinery)" lines, 0 FAIL; 299 - 11 = 288 |
| 38 | Normal run keeps exactly 4 files in the work folder | `08-main-run-rc.txt` shows `files=4` for both runs; self-test case "the kept folder holds only the output copy and the rule files (4 files ...)" |
| 39 | Git index same sha256 and modification time before and after a normal run | `09-git-index.txt` (sha256 4e484a54..., mtime 14:02:29.304811991 both) |
| 40 | Exit codes 0, 2, 3, 4, 129, 130, 141, 143 and the `--self-test` 0/1 | script header line 44, trap lines 79-80, `exit 2/3/4` lines 877-1299; `05-signals.txt` shows 129/130/143 with no folders left |
| 41 | Block names R00, Q23-1 to Q23-4, Q27a, Q27b, Q27c, G35, G06, G04, G18, G36, G37-38, G07, G20 | all present in the script (lines 1131-1269) |
| 42 | Search words: `window\|end_date\|not_after\|deadline\|need_seconds\|2026-11-2\|refus`; settings-line words end, window, deadline, until, not_after with date-or-number rule; `find -maxdepth 4`; Q27a "with 20 lines after each" and case-sensitive; Q23-3 case-sensitive; delete-word pieces | script lines 897-912, 1176-1184, 1189-1217, 1166-1169 |
| 43 | Environment variables `TAKE_PY CRM_PY DRIVE_PY N8N_PY FLOWS_DIR MODEL_DIR MODEL_SETTINGS ONE_STORE LEAD_REPIN_NO_STATUS END_RE MODEL_RE DELETE_RE`, `SELFTEST_FILTER` (only in `--self-test`), `LEAD_REPIN_TEST_BREAK_FILTER=weak\|empty`; git switches `--no-optional-locks`, `-c core.fsmonitor=false`; `umask 077`; `mktemp` form `lead-repin.XXXXXX` | script lines 6-10, 38-59, 891-899, 1104 |
| 44 | Tested only with GNU sed 4.9 and mawk 1.3.4, as root | `v4-CHANGES.md` line 42; versions on this machine: GNU sed 4.9, mawk 1.3.4 |
| 45 | `--mask` damaged-filter case, identity (cat) filter makes `--self-test` fail | self-test machinery lines in `03-selftest-*.txt` |
| 46 | Banned-string count: no `sk_live_`, no `ghp`, no AKIA literal other than the example in the guide | `10-banned-count.txt` line 2 (guide file: 0 / 0 / 0) |
| 47 | sha256 of the guide and the script | `11-sha256-script-doc.txt` equals what `sha256sum` prints now (script e779c774..., guide f5913d49...) |
| 48 | "sed, awk, grep ... Windows listeners not seen from WSL" etc. (tool facts) | no file to cite; not counted |

(Row 48 is a note and is not counted. Several OK rows group more than one cited item; every grouped item was opened, and none of the WRONG or UNREADABLE items is hidden in a grouped row.)

## Counts the lead's brief asked about that the guide does not state

- "108 signal runs": the guide does not state this number. The evidence has 108 lines with `exit=` in `evidence-repin4/05-signals.txt` (matches the checkpoint note and the lead's figure).
- "12 mutations": the guide does not state this number. `evidence-repin4/06-mutations.txt` shows 7 mutants (m1 to m7), each run under dash and bash = 14 lines. Six are killed (self-test fails or exits 1); m3 (`self_test` return forced to 0) is NOT killed and the file's own note calls it an equivalent mutant. So "12 mutations" does not match this file (7 mutants, 14 runs, 6 mutants killed). `v4-CHANGES.md` line 27 speaks of "the 3 mutations v3 missed" and does not give 12 either.

## Housekeeping

- No file outside `handover/core-hardening/lead-repin/` was edited. `find` shows no `__pycache__` in the lead-repin folder. (`steps-edits/__pycache__` exists from other work and was not touched.)
- The script itself contains `BEGIN PRIVATE` text once and 9 e-mail-shaped strings (per `10-banned-count.txt` line 1); these are canary test inputs, not real values. Not a citation problem.
- No banned vendor brand strings were written in this file.
