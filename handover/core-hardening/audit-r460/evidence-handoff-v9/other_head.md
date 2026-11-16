# Core hardening hand-off v9, other tracks (everything that is not spend), 2026-11-16 UTC (same date in IST)

Companion of `CORE-PR-HANDOFF-v9.md` (the spend track). Split made on the lead's answer Q33 option (b). The content of v8 sections 4.6 to 4.11 is copied by script from `CORE-PR-HANDOFF-v8.md` (exact lines 550-636, `evidence-handoff-v9/mk_other.py`), then changed only where a review finding or a rename says so (list in section O-3 and in `v9-CHANGES.md`). Inside the copied text, "4.x" means section "O-4.x" here, "E0-n" is a v8 evidence id (the v9 ids are in section O-7), and "D n" and "F n" are the rows of sections O-1 and O-2.

**Core is paused for the customer demo (answer Q28). Nothing here blocks the demo, nothing here may be built before two independent reviewers have read it, and every owner step is POST-DEMO and needs a new owner yes.** Status of every item: **specified, unverified** (written from code I opened; nothing run).

## O-0 What failed, what is uncertain, what was not run (read first)

1. Nothing was run except small read-only programs (`evidence-handoff-v9/`). No test suite, no `ruff`, no `bandit`, no Postgres.
2. **The lead's order and this task's brief disagree about seven PRs.** The lead's wording was to drop PRs whose per-item verdict (the lead's own "needed-check" list) is NOT-NEEDED or DUPLICATE; the brief says to carry them over unchanged. I followed the brief. **That verdict is not supplied** for any item below: my inputs contain no per-item verdicts (grep of `ORDERS.md` and `MASTER-MAP.md`, `raw-greps-v9.txt`). Every item carries the line "needed-check verdict: not supplied". The lead decides which items stay.
3. The copied sections 4.7 to 4.10 are a copy of text that three reviews read; v8 reviewed it as part of a larger document. Findings that touch them are applied (O-3). The security review's major about the extract schema guard is already in the text (4.7, the schema guard).
4. Vendor and database facts: none of these items rely on one except H-1 (S3 Object Lock behaviour, UNVERIFIED, see O-7 E0-O8).

## O-1 Decisions that these tracks need (from v8 section 3, unchanged except where marked)

| Id | Question | Answer in force |
|---|---|---|
| D2 | G4: wording or behaviour first | Wording first: G-W merges before G. |
| D3 | Are `get-secret-value`, `get-session-token` read-only in approval text | Default no, withheld (row G5a). If the lead says read-only, drop the row. |
| D4 | Refuse signer or anchor kind `none` in pilot | Warn only until decided; owner; POST-DEMO. |
| D6 | Old stage name | Follow R449: refuse the old name, rename to `demo`. Alias default: none. |
| D16 | Lowercase bare SQL | Shown unless a code marker is present (rule G3). |
| D17 | Redaction base64 second pass and speculative patterns | Deferred; a pattern ships only if its canary leaks on old code. |
| D18 | Anchor-writer identity split, outbox alert age | Deferred to the first pilot config; H-1 writes the `anchor_s3.py` docstring. |
| D21 | Upper-case or `.EXE` program names | Dropped: `channel.clean` defangs the dot; a display change, not a leak. |
| D22 | PDFs and images in `extract()` | Always refused; trigger: first client build needing PDF adds a text kind in front. |

Every row: needed-check verdict not supplied.

## O-2 Facts used (v8 numbering kept; read in v8, cite lines machine-checked in v9)

| # | Fact | Source |
|---|---|---|
| F1 | G4 is a display filter: it swaps commands in model-written approval text for `[command withheld (G4)]`; it does not decide whether a tool runs. | `approvals/gate.py:681-698` |
| F2 | `_WRITE_SHAPES` is one compiled regex with no global ignore-case; SQL words are upper-case only. | `approvals/gate.py:647-678` |
| F10 | `extract()` has no non-test caller in `src/`; recorded fake replies are keyed on `sha256(documents[0])` when documents exist. | `llm/fake.py:39-40` |
| F11 | `Verification`, `verify_rows` and `audit_verify` as 4.6 describes. | `audit/chain.py:134-149`, `:363-383`; `cli.py:349-363` |
| F12 | `mounted_file._fetch` checks; `signer.py` has no checks. | `actions/secrets_file.py:34-64`; `audit/signer.py:104-108` |
| F16 | `DeadLetter`, `Valid`, `runmap` functions as 4.7 describes. | `models.py:218-222`; `extract.py:18-25`; `guard/runmap.py` |
| F17 | `injection_check` catches every `Exception` (spend track edits it to re-raise `SpendRefused`; this track does not touch it). | `guard/injection.py:85-101` |

## O-3 What v9 changed in the copied text (review findings applied)

- Fileguard PR renamed **K1** (v8 called it S1, which clashed with the spend PR S-1 of the spend track).
- The "I did not search" sentence in O-4.8 now states the grep that was run and its result.
- The test-module rule for the later spend gate (module-prefix "starts with tests") is a spend-track matter and is gone there; nothing in this file uses it.
- Evidence rows are rewritten as runnable commands (O-7): test path or script, output file, pass rule, author PR, no circular dependency; the bandit command is the one of `.github/workflows/ci.yml:119`.
- Times: all dates are UTC with IST beside the clock times that matter (none of these items has a clock time).

