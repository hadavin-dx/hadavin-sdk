# fix-review19: batch on `reviews-of-core-patches/REVIEW.md` (fixer, uncapped security path, one batch)

Edited only `REVIEW.md` and this log. `patch-copies/` untouched (another fixer owns it). Nothing committed.

## NOT verified (read first)
- Every Postgres statement and every host behaviour (CODEOWNERS, branch rules, managed-database administrator roles, `VALID UNTIL`) is UNVERIFIED: nothing was run on Postgres or a host.
- Day figures in Decisions 27 and 29 (3 to 6 days) and the cost words in Decisions 12, 26, 27 are assistant judgement, not measured.
- The SQL and exact columns for the new dead-man reads (signed-head age, oldest outbox row) are not written or checked.
- I did not re-read every History paragraph; I did not read `fix-review12.md` (a search found 'Round 19' once in it).
- Not every reader item was given its own long rewrite: reader M6/M7/M13 and design M6 were handled by short edits (round tags removed from live text, 'owner' terms split, UTC with IST added); I did not re-read the whole 600 lines after editing, only ran the scripts and greps below.
- Rating changes (X-6.6d to Major) are a PROPOSAL; no count changed.

## Findings
| Finding | Result |
|---|---|
| Reader B1-B3 | Answer order now 26, then 27, then 28, then 2 (needs 26 and 27); Decision 28 'no' stated under Decision 1 options 1 and 2; Decision 27 says when the binding must exist (before the pilot, or before the proposal if the head wants it) with consequences. |
| Reader B4 | Q1 rewritten in plain words: what the recorded take is, where to look (`inputs/DECISIONS-2026-11-16.md` items 1 and 7, the run sheet, the flow files), three answers, a safe 'I do not know'. |
| Reader M1, M10 | 'Does not sign' is decided only in Decision 29 (one size, one consequence of 'no'), scoped to production (read: `config.py:419-420`, `backends/table.py:604`, `stages.py:18-23`); other places point to it. |
| Reader M2, design M2 | Decision 27: options with cost and risk; 'signed subtree' defined; key custody (no agent session holds the approval key); reuse of `Signer` and `verify_signature` in `audit/signer.py` and the signer kinds. |
| Reader M3, design M4 | Decision 26: notes live in the client's own repository or an outside store, per client code; core-only notes in `handover/acceptance-notes/`; cites `no-lost-messages-isolation-load.md` item 2 and 7, R373; changing the rule needs the head's yes. |
| Reader M5 | One definition of drain (move plus delete, `chain.py:232-246`); 'the tick drain step' and 'the drain program' named separately. |
| Reader M6 | Round numbers and 'withdrawn' remarks removed from live text (0 matches left); a History note records it. |
| Reader M7, M8, M9 | 'owner' compound terms split (code owner, folder owner, table owner); 'login table' fixed, 'identity table' kept only in a glossary note; one READ THIS FIRST line added. |
| Reader M11, M12, M13 | Decision 12 cost of yes written; stale count at the old line 112 fixed (29 numbered, 9 and 23 asked in two parts: 27 + 4 + 2 = 33); IST added to the UTC dates that lacked it. |
| Reader P1, P2 | The quote '9394 = 9364 + 30' is cited by README section name; log list in History names `fix-review16` to `19` in `../reviews/`. |
| Design M3 | Decision 25: deployer is a human or CI job on short-lived federation, never an agent session; `operator` stop/reset split offered as options (a) and (b), not chosen. |
| Design M5 | Paragraph on liveness per process (checkpoint step green with no signer, `tick.py:177-181`, `chain.py:299-300`). |
| Design M6 | Five undeclared-login gaps listed as design items; name mismatch `dead-man reader` / `deadman_reader` stated. |
| Design M7 | 9b value statement added; 'no, for now' with a note is offered. |
| Design M8 | Rule text corrected for the D-3 carve-out; X-6.6d Major proposal with its effect (Major parts 9 to 10, items 11 to 12; rows stay 4/13/11). |
| Design M9 | 'Who decides what' written as a proposal to the head. |
| Citation review 4, 7 items | Fixed (README cited by text or section name). |

## Where a reviewer was wrong
- Citation review: 'README (a) to (e)' was wrong; the README has clauses (a) to (d).
- Design M8 arithmetic: counts 10 Major parts and 12 items follow only if X-6.6d is counted as a separate part; under the counting grain it sits inside X-6.6, so I state the effect as a proposal and changed nothing.

## For the coordinator
README of `patch-copies/` line 36 still points at 'REVIEW near its line 384 to 390'; that is stale. I did not touch it (another fixer owns it).

## Command output (from `handover/flows-audit`)
- `count_review.py`: rows 28; Major 4, Minor 13, Nit 11; PROPOSE FIX 25, DECLINE 3.
- `tools/check_refs.py`: PASS 5176 references.
- `tools/check_names.py`: PASS 655 rows.
- `tools/check_secrets.py`: PASS 0 hits in 2054 files.
- `ruff format --check .`: 765 files already formatted.
