# Citation review 40 (read-only check of REVIEW.md against the repo)

Checked: `REVIEW.md` (804 lines) against src (equals commit 176a0cbe0), tests, ci.yml, migrations, `patch-copies/*.patch`, ORDERS.md, `../inputs/DECISIONS-2026-11-16.md` and `../heavy-test-lane/*`. No build or test was run. Method: all `path:line` cites were extracted by script, bare file names resolved to `src/hadavin_sdk/...`, then (1) file exists and line in range, (2) backticked names in the claim compared with the cited lines, (3) every flagged or name-less cite read by hand.

## Failures and what was NOT checked (first)

MISMATCH (4):
1. `patch-copies/README.md:8` and `DEAD-MAN-CHECK.md:3` quote `../REVIEW.md:5` as "the C-01 extras (the **token ceiling**) are CUT". REVIEW.md:5 reads "(the **token limit**)". One word differs, so the "word for word" claim is false. Fix: change "ceiling" to "limit" in both files, or quote differently.
2. `limits.py:43-52` and `limits.py:48-52` (cited in REVIEW.md): the file has 51 lines, so line 52 does not exist. Fix: cite to 51.
3. `test_p2_postgres.py:289`: described in REVIEW.md as a migrate call. Line 289 is `assert migrate(fresh_dsn) == [...]` (the assert on its result), and the migrate call is inside that expression, so the description is loose rather than wrong. Fix: say "the assert on the migrate result".
4. (Weaker) A cite made from the `:77` side: README.md and DEAD-MAN-CHECK.md both say "line numbers move, find it by text". Line 77 of REVIEW.md still starts "3. C-01: DO NOT APPLY NOW", so that cite is OK (see MATCH below). REVIEW.md:310 mentions `../REVIEW.md:67` but states the correction itself (it was one line off, text is the anchor, 77 is current). Not a defect; recorded so nobody reads :67 as live.

NOT CHECKABLE:
- Every cite tied to commit b4cce5b or to patched `/tmp` copies: b4cce5b is not reachable in this shallow clone and the /tmp copies are gone. Their numbers (line numbers in the patched files, any count that depends on running the patched code) were not checked.
- The `G5-wording.patch` file: not present in `patch-copies/` in this clone, so cites into it were not checked.
- Measured numbers that need a run (full-suite totals such as the 9364 baseline at `patch-copies/README.md:377`, timings): they restate files in `../heavy-test-lane/` (SUMMARY.md, evidence-*.md). I confirmed the restated figure matches those files where I found it; I did not re-run anything.
- 127 cites carry no identifier in the claim; I read them by hand but the judgement "line shows what the claim says" is mine, not a script's.
- REVIEW.md lines 787 and 796 (29 KB and 48 KB single lines) were searched for cites by script, not read line by line.

## Table

| Cite | Claim | Result |
|---|---|---|
| `REVIEW.md:5` | Starts with the words quoted by README.md:8 and DEAD-MAN-CHECK.md:3 | MISMATCH (quote says "token ceiling", file says "token limit") |
| `REVIEW.md:77` | List item starts "3. C-01: DO NOT APPLY NOW" | MATCH |
| `REVIEW.md:77` | C-01-price-only.patch is 78 lines, hunks `@@ -362,6 +362,16 @@` and `@@ -0,0 +1,51 @@` | MATCH (hunk header seen in patch; test file hunk is 51 lines) |
| `REVIEW.md:310` | cite `:67` was one line off, 77 is current | MATCH (the text says so itself) |
| `limits.py:43-52`, `limits.py:48-52` | code at those lines | MISMATCH (file ends at line 51) |
| `limits.py:20-29`, `:46` | `blocked()` reads kill switch and spend, no write; `write_outcome` on stop | MATCH |
| `test_p2_postgres.py:289` | migrate call | MISMATCH (loose: it is the assert on the migrate result) |
| `tools.py:494` | spec deep copy | MATCH |
| `app.py:84-85`, `:87` | `restored_hash_key_secret_name` required in pilot and prod; purge role comment | MATCH |
| `app.py:151-160` (incl. `:156`) | purge store built from `purge_dsn_secret_name` with a second connection | MATCH |
| `app.py:250-264` | `purge_store=` passed, `_own_secrets` limited to the tool's `secret_names` | MATCH |
| `backends/table.py:120`, `:502-503`, `:529`, `:545`, `:604` | `purge_dsn_secret_name`, audit local_dir entry, openai_compat entry, llm_judge comment, `NOT_PROD` set | MATCH |
| `stages.py:18-23` | `is_prod` is True for anything except demo and pilot | MATCH |
| `llm/common.py:59-62`, `:169` | `estimate_tokens` is len//3, min 1; cost divides by 1,000,000 | MATCH |
| `llm/common.py:150` | line content | MATCH by neighbouring context (the line itself is blank) |
| `models.py:141`, `:196`, `:256-259`, `:294-302` | `model_copy` UTC, `event_id` default factory, `KillSwitch`, `Reply` fields | MATCH |
| `evals.py:80` | `cost += reply.cost_usd` | MATCH |
| `store/memory.py:76-81`, `:175-180`, `:196-198` | `add_cost`, `get_approval_decision`, `add_spend` | MATCH |
| `approvals/receiver.py:30`, `approvals/channel.py:29`, `guard/redact.py:16` | `record_only=True` receive, `redact_text` with `_neutralise`, HIGHENTROPY/G5 text | MATCH |
| `approvals/gate.py:3`, `:203`, `:206`, `:354` | copied-from header, ZWSP/G5 comment, `_UNVERIFIABLE` | MATCH |
| `audit/local_dir.py:116-128`, `:121`, `:126-128`, `:143-156` | outbox write via `os.replace`, `reconcile` drains and moves corrupt files | MATCH |
| `audit/protocol.py:27` | `reconcile() -> int` | MATCH |
| `actions/secrets_env.py:1` | env secrets, demo only | MATCH |
| `C-01.patch` hunk 2 (about lines 14-30, 75) | `raise ValueError("routes with a zero or negative price...")`, `@@ -362,6 +362,16 @@` | MATCH |
| `A-01.patch:12, 25, 60, 72` | `_LOG.warning` / `_LOG.error` calls | MATCH |
| `../inputs/DECISIONS-2026-11-16.md:5` | item 4 (A-01 deferred, extras cut, G5 kept) | MATCH |
| Login count 12+5-1=16, 8x2=16 lock signatures, 11 fixed signatures | arithmetic stated as measured | MATCH on arithmetic; the underlying counts come from evidence files and were not recomputed |
| Remaining ~460 cites (resolved by script, identifier found on the target line) | claim names appear on the cited line | MATCH (heuristic; 463 passed automatically, 236 flagged and read by hand, flagged ones resolved as MATCH except those listed above) |
| All cites tied to commit b4cce5b or patched /tmp copies | line numbers in those versions | NOT CHECKABLE (shallow clone; /tmp copies gone) |
| Cites into `G5-wording.patch` | content | NOT CHECKABLE (file absent from clone) |

## Honest limit of this review

The table groups hundreds of matches by file rather than listing each one, and the grouped MATCH rows rest on a name-on-line heuristic plus my reading of the flagged ones. I did not re-run any measured number. The patch-line cites above were the last items verified, and I wrote this file after a context reset, so the per-row detail for the earliest-checked cites is from my summary notes, not re-read just now.
