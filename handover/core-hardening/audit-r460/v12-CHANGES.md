# v12 changes: spend track and other tracks, 2026-11-16 UTC (IST = UTC+5:30)

**Read first: failures, gaps, what was not run.**
- **Nothing was run.** No test suite, no `ruff`, no `bandit`, no Postgres, no vendor call, no spend. All designs are "specified, unverified". Only reads, small read-only programs and `bash -n` were run (raw output in `evidence-handoff-v12/`).
- **`evidence-handoff-v12/gate4.sh` was never run.** It was syntax-checked with `bash -n` (`raw-gate4-syntax.txt`) and compared line by line with `ci.yml` (`raw-gate4-vs-ci.txt`). It does not set the CI test settings (`HADAVIN_TEST_PG_DSN`, `HADAVIN_TEST_VAULT_ADDR`), the dependency install, the `psql` check or the CI security job; the header lists them. A green laptop run is weaker than CI.
- **Open risks stated, not fixed (each has an owner or a PR):** a 429 or 5xx storm can use up the day (release-on-429 needs the owner's yes, question O1); DB-1 does not close the runtime role's `UPDATE` on spend tables and the kill switch (L-2, POST-DEMO; the decrease record only shows it afterwards); the guardrail price per unit is an operator statement (5.9 row 7); vendor billing facts, the error shape of each SDK, Postgres behaviour, the wheel contents and the paid detector kind names are UNVERIFIED.
- **A slip of mine in v11, corrected:** v11's change list said the gate's retry owns guardrail repeats; v11's section 5.7 gave the guardrail no retry. v12 says plainly: there is no gate retry for the guardrail (5.7).
- The EGM skills were not invoked (brief). The two lines of the standard review (zoom-out, security) of v12 are still to be run by the lead.
- The `Q34` clause `usd < 'Infinity'` is my addition to the lead's `usd >= 0`; the fall-backs are in 5.6 and question L7.

## Readiness review (7 majors, 9 minors)

| Finding | Fix | Where | Test (fails on old) |
|---|---|---|---|
| M1 no handler for `SpendRefused` in S-1 | minimal handlers in S-1 at four sites; S-2a replaces the `Runtime.handle` one | spend 5.2b | E0-S1-3 (c) to (f), no stub-less old code can pass |
| M2 E0-S1-3 needs a stub | `tests/spend_support.py` with `NetworkStub` moves to S-1 session 2; S-2a adds the fixture | spend 7.1, 7.2 | E0-S1-3 |
| M3 exact signatures, audit owner | `GateSettings`, `Reserver`, `CallGate.__init__/admit/settle/keep/release`, `build_window`, `build_gate`; audit rows through `Reserver.note` (`Limits.note` writes an audit row, `ProcessCap.note` only a log line) | spend 5.3 | E0-S2-4 |
| M4 merge order of 13 ids, rebase, "four small PRs" | combined table, rebase rule, hot files, start gates G-1 to G-4 and NC-1; the sentence is withdrawn | spend 7.1 | none (text) |
| M5 `gate4.sh` path, outputs, uv, CI env, "four"/"five" | rewritten script (root found itself, outputs in the evidence folder, `uv run --all-extras --group test`, five commands, header lists CI differences) | `gate4.sh`, spend 7.2 E0-S1-1, other-tracks O-7 | `bash -n`, `check_gate4_vs_ci.py` |
| M6 DB-1 seam, ledger gap, owner-yes format, packaging | `migrate(folder=)`, unnumbered held files that take the next free number, `OWNER_YES` = role, date, sha256, wheel listing | spend 5.6 item 1 | E0-DB-1 (scheduled) |
| M7 R, G, H-2 grammar, self-dependency, G5a | canary grammars (UNVERIFIED), R and G write their own test files first, G5a ships (D3 = no), H-2 named scope | other-tracks O-4.9, O-4.10, O-4.11, O-6 | E0-O4, E0-O6, E0-O12 |
| Constants, NEEDED-CHECK details | all constants added in S-1; the lead saves the file, evidence kinds, `LEAD-DECISION:`, deadline 2026-12-31 | spend 7.1, other-tracks O-6 | none |
| m1 minutes | marked as estimates | spend 7.1 | none |
| m7, m8 | `KEY_FILE_MAX_BYTES = 65536`; S3 probe call `get_object_lock_configuration` (UNVERIFIED) | other-tracks O-4.8, O-4.11 | E0-O2, E0-O8 |
| Cites | 78 ANCHOR-MISS read: all prose words in backticks, not wrong cites; 62 bare `:N` given paths by `fix_ambig.py`; a wrong file for line 513 corrected | both files, `raw-cites-v12.txt` | cite check |
| llm group count | method stated: additive merge 9 today, 10 planned; replace merge 9 (not used); by package 11/10; no group without type-only imports | spend 8.1 | `raw-cycles-v12-independent-script.txt` |

## Security review (5 majors, 9 minors)

| Finding | Fix | Where | Test (fails on old) |
|---|---|---|---|
| F1 `AnyOf` swallows the refusal | `_SPEND_MODE` ContextVar; `AnyOf` forwards the mode | spend 5.5 | E0-S2-4 two detectors; mutant `AnyOf` default |
| F2 Bedrock release unreachable | `status_of` hook, Bedrock override | spend 5.3 | E0-S2-4 real offline-built errors; mutant |
| F3 429/5xx storm | kept by default, audit row `spend_kept_after_failure`, off-by-default `RELEASE_EXTRA_STATUSES`, question O1; open availability risk | spend 5.3, 5.9 row 8, section 10 | E0-S2-4 both settings |
| F4 guardrail flat price | per-unit price, `max_chars` bound, `prompt_too_large`, 5.9 row 7 | spend 5.7 | E0-S2-4 |
| F5 runtime UPDATE not closed | stated; decrease record file as interim; kill switch exposure stated; L-2 real control | spend 5.6, L8 | E0-DB-1 |
| F6 AST census | census C6; C5 literal only; "client build fails" withdrawn | spend 6 | E0-S1-6 |
| F7 owner gate | sha256 pin, role and date, CODEOWNERS, sonar exclusion, "tripwire" wording | spend 5.6 | `test_owner_gated_migrations.py` |
| F8 CHECK, repair | needs Postgres 14; repair only with the kill switch on | spend 5.6 | E0-DB-1 |
| F9 wrong code | `call_retry_budget` | spend 5.3, 5.5 | E0-S2-4 |
| F10 `ScopedDetector`, wording | token reset, nested test; distinct `spend_refused` card wording | spend 5.5 | E0-S2-4 |
| F11 guardrail one request | measured flag rate | spend 5.7, E0-S2-7 | E0-S2-7 |
| F12 rounding, guardrail retry | `call_cap` rounds down (reservations up); retry statement corrected | spend 5.1, 5.7 | none |
| F13 canaries | E0-S2-9 | spend 7.2 | E0-S2-9 |

## Not checked
Everything under "Not checked" in section 10 of the spend file, plus: the other-tracks content beyond the edits listed in its O-3 "v12 edits" bullet (copied unchanged), the hot-file overlaps beyond the files I read, and whether the lead agrees with the 13-id merge order.
