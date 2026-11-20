# core-a -> core-b (and core-c): B8-text, the door text for README.md, SECURITY.md and CHANGELOG.md (steps D and E, ORDER 015 facts)

Written 2026-11-20 by core-a (task A4 from the lead). It replaces the PR package of about 13:00 UTC. It also supersedes four sentences of core-a's older request `handover/core-a/requests/002-readme-security-text.md`: R-1, R-5, R-9 and S-6. They say "default 1", "no connection cap", "not run in n8n" and "fallback numbers". None is true any more.
Why a request: the root README.md, SECURITY.md and CHANGELOG.md belong to core-b and core-c. core-a edits none of them. Everything below is text to paste.
Words: "the door" is the signed trigger endpoint and its worker. NEEDS_PERSON is the run state that asks a person to look. "The tick" is the scheduled step that ends stuck runs. "E-door-1" is an owner decision in `handover/core-a/ESCALATIONS.md`: what an acknowledged but cut-off run is worth. Option A (the sender polls) is the default, and the text says A.

## 1. What to paste where

The three files with proofs are in `handover/core-a/pr/`. Every `[path:line]` in square brackets is a proof for the coordinator; strip it before pasting. `integ:` in a proof means the merged tree /home/user/wt/integ.

| File to paste | Where | Source text |
|---|---|---|
| SECURITY.md | a new section "The signed trigger door: what it guarantees and its stated limits (reviewed, not bugs)", after "Stated limits of redaction (reviewed, not bugs)" and before "Spend limits (stated limits)" | `handover/core-a/pr/SECURITY-door-section.md`, from the heading down |
| CHANGELOG.md | the bullets under `### Added` in `## Unreleased`, after the `limits set-cap ...` bullet | `handover/core-a/pr/CHANGELOG-lines.md`, the 17 bullets (the paste note at its top is not text to paste) |
| CHANGELOG.md | do NOT add a second `triggers.conflict_events_per_minute` bullet: the existing one (CHANGELOG.md:13) is right once the worker reads the setting | see section 3 |
| README.md | a new section "Signed trigger door (limits)", after "Limits and trust (K5 read tools)" and before "Spend limits: what is in force today"; text in section 2 below | this file |
| n8n/README-trigger.md | the four blocks of `handover/core-a/pr/README-trigger-postmerge.md`, applied only after core-b's `TriggerSettings` and limits are in the tree | that file |
| n8n/README-trigger.md | nothing for queue mode: the statement is already in the file (lines 209, 393, 883) | `handover/core-a/pr/README-n8n-queue-mode.md` |

## 2. README.md section text (new; core-b pastes it as written)

Heading: `## Signed trigger door (limits)`

- One signed POST starts at most one run per key. The answer is sent only after the run row exists: 202 while the run is RECEIVED or WORKING, 200 in any later state. [src/hadavin_sdk/triggers/worker.py:1-6; src/hadavin_sdk/triggers/worker.py:549-558]
- A 200 does not mean "ended". PLAN_READY, WAITING_FOR_APPROVAL, EXECUTING and VERIFYING also answer 200. [handover/core-a/CRASH-MATRIX.md:120]
- The same key with another document is a 409 and starts nothing. Renaming the tenant or a sender changes every run id, so an event already handled runs again when it is sent again. [src/hadavin_sdk/triggers/worker.py:549-556; src/hadavin_sdk/triggers/endpoint.py:168]
- A run that is cut off after the 2xx ends as NEEDS_PERSON with no notification and no stored document. The sender must poll the run state. There is no read address: polling means sending the same signed key and document again. [src/hadavin_sdk/triggers/worker.py:36-39; n8n/README-trigger.md:617-626]
- The worker needs a `triggers:` block in `config.yaml`. `max_running` (default 4) and `conflict_events_per_minute` (default 10) are read from it only. This is true only on the merged tree. [src/hadavin_sdk/triggers/worker.py:714-721; integ:src/hadavin_sdk/defaults.py:280-287]
- Exit codes: 0 clean stop, 2 refused configuration, 3 any other start failure. A store that is down at start is not an exit: `GET /health` answers 503 until the store returns. [src/hadavin_sdk/triggers/worker.py:125; src/hadavin_sdk/triggers/worker.py:947-1008]
- The memory store is refused outside the `demo` stage. [src/hadavin_sdk/triggers/worker.py:669-682]
- A reverse proxy with per-peer connection limits is required, and it ends TLS. The server has 256 global connection slots and no per-peer limit. It listens on 127.0.0.1 unless `--allow-non-loopback` is given. [src/hadavin_sdk/triggers/worker.py:42-43; src/hadavin_sdk/triggers/server.py:54; src/hadavin_sdk/triggers/worker.py:630-634]
- One secret per tenant and per stage: the tenant is not in the signed string. [src/hadavin_sdk/triggers/worker.py:44-45]
- The n8n template under `n8n/` ran once, in n8n 2.47.7. n8n queue mode is recommended and NOT verified. [n8n/README-trigger.md:3; n8n/README-trigger.md:209]

## 3. Which of core-a's statements are true only on the merged tree

core-a's own branch has no `TriggerSettings`, no `Limits.reserve` and no `hadavin_caps` seeding. These statements are true only on the merged tree (core-b config and limits present):
- `max_running` default 4 and ceiling 64, `conflict_events_per_minute` default 10 with range 1 to 1000, and the bounds checked at config load with exit 2 on a bad value. [integ:src/hadavin_sdk/config.py:395-425; integ:src/hadavin_sdk/defaults.py:280-287; integ:src/hadavin_sdk/config.py:709-717]
- The worker reads both numbers from `config.triggers` and holds no second default. On core-a alone a settings object lacking either field is a start error (exit 2), so the worker cannot start there. [src/hadavin_sdk/triggers/worker.py:714-721]
- The main model call of a run reserves before the call and settles after it, so parallel runs cannot overshoot a cap through that call. [integ:src/hadavin_sdk/runtime/agent_loop.py:567]
- The start warning about `max_running` above 1 fires only when the limits have no `reserve`; on the merged tree it never fires. [src/hadavin_sdk/triggers/worker.py:685-696]
- The crash matrix reads the money end state per kill point only when `Limits.reserve` exists. One open hold stays open until expiry. A restarted run never books again. The day total equals the sum of the rows. The child's seeding widens `max_day_skew` and `min_expiry_age`, so the real day window and the 3600 second expiry floor are not exercised. [tests/triggers/crash_launcher.py:18-26; tests/triggers/crash_launcher.py:58-60; tests/triggers/crash_money.py:1-20]
- `tests/test_trigger_config.py` and the strict-mode tests need core-b's `TriggerSettings`; without it 10 tests fail by design under `HADAVIN_REQUIRE_PG=1`. [handover/core-a/evidence/BATCH10-summary.md:1-20]

True on core-a alone as well: the header cap (16382 bytes, then 431) and the HTTP refusal contract (400, 414, 431 in one write with `Connection: close`). Also the memory store refusal outside `demo`, exit codes 0, 2 and 3, the in-process recovery from a degraded start and `GET /health`. Also the `trigger.conflict` event cap per sender, and the 43 plus 171 crash points on the older add-spend tables. [src/hadavin_sdk/triggers/server.py:240-256; src/hadavin_sdk/triggers/worker.py:669-682; src/hadavin_sdk/triggers/worker.py:1060-1080]

Figures that are quoted, not new: the last full mutation run is in `handover/core-a/evidence/mutants-run19.md` (120 of 120 expected at 5a8c83fd3). The text says "see evidence/mutants-run19.md and run 20 when it lands" and gives no run 20 number, because run 20 has not finished. When it lands, core-a or the coordinator replaces that phrase with the number read from the file.

## 4. Contradictions between the root documents and the code (core-b and core-c must fix; from `handover/core-a/DOCS-CONSISTENCY-1.md`)

Read on the merged tree (core-b 463760813, core-a d1ee703ab, core-c bd7f9d978, head 6c89f0495). core-a changes none of these files.

| # | File:line | What the text says | What the code does | Owner | Fix |
|---|---|---|---|---|---|
| 1 | SECURITY.md:23-25 | `migrate --runtime-role` does not refuse a runtime role that owns the audit tables | `migrate` refuses a runtime role that owns a relation and rolls back [integ:src/hadavin_sdk/store/migrate.py:446-449; integ:src/hadavin_sdk/store/migrate.py:1337-1340] | core-b | rewrite the tamper-evidence text: condition (1) is now enforced by `migrate` for the named runtime role |
| 2 | README.md:58 | "migrate does not yet refuse a runtime role that owns the tables" | same code as row 1 | core-b | same rewrite |
| 3 | SECURITY.md:28 | wider rights are tracked in `handover/core-b/tickets/A-audit-rights.md` | DOCS-CONSISTENCY-1 reported the file missing; core-a found it present in the integ checkout [integ:handover/core-b/tickets/A-audit-rights.md:1]. It lives under the internal `handover/` folder, which the merge dry-run excludes [handover/core-a/INTEGRATION-DRYRUN-2.md:1] | core-b | point to a document that ships (docs/ or SECURITY.md itself) or drop the pointer |
| 4 | CHANGELOG.md:9 | "0007 to 0011 are unreleased and may still change" | 0007 is released and hash-pinned: `docs/migration-checksums.md` says "Released files (0001 to 0007)" and `migrations_released.json` pins them [integ:docs/migration-checksums.md:8; integ:src/hadavin_sdk/store/migrations_released.json:1] | core-b | say "0008 to 0011 are unreleased and may still change" |
| 5 | CHANGELOG.md:13 | `triggers.conflict_events_per_minute` caps `trigger.conflict` events per sender | was dead on the merged tree (the worker passed its own constant 10); core-a's d-fix24 now reads it from `config.triggers` [src/hadavin_sdk/triggers/worker.py:717-721; tests/triggers/test_d_fix24_conflict_setting.py:58] | core-b text, core-a code | no text change; true once core-a's worker is merged |
| 6 | cli.py header | omits exit 5 of `limits release-expired` | exit 5 exists (DOCS-CONSISTENCY-1 row 10) | core-b | nit: add exit 5 to the header |

core-c: no door-related contradiction was found in core-c's text. One thing core-c should know: the model gate is not yet installed in `Runtime`. The "ungated sites" list in "Spend limits" therefore stays as core-b wrote it, and the door text only points to it. [integ:CHANGELOG.md:8]

Items 5 to 9 of the DOCS-CONSISTENCY-1 contradictions list are core-a's own and need no action by core-b or core-c. They are the README-trigger lines 51-54, 803-806 and 675-677, the "One run at a time" heading, the worker module text on spend, and the evidence citations. The README-trigger fixes are in `handover/core-a/pr/README-trigger-postmerge.md` and apply only on the merged tree. The module text is already fixed in `src/hadavin_sdk/triggers/worker.py`. [handover/core-a/DOCS-CONSISTENCY-1.md:18-19; src/hadavin_sdk/triggers/worker.py:27-31]

## 5. Claims core-a could not verify (so they are not stated as fact)

- A run of the crash matrix on the merged tree with the real PostgreSQL day window. The text says the child's seeding hides it.
- That the ungated sites other than `_screen` (shadow cards, `k1b`, evals) are charged as core-b's text says: core-a read `_screen` only. [integ:src/hadavin_sdk/runtime/agent_loop.py:388-392; integ:CHANGELOG.md:8]
- Mutation run 20 (no number is quoted) and any whole-suite run on the merged tree after the last door edits.
- n8n queue mode, n8n Cloud, anything on Windows.
