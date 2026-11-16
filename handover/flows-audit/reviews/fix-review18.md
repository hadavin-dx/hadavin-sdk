# fix-review18: round 25 batch on `reviews-of-core-patches/REVIEW.md` (fixer, uncapped security path, one batch)

Edited only `REVIEW.md` and this log. `patch-copies/` untouched (another fixer owns it; no number copied from `fix-patchcopies5.md`, which did not exist). Nothing committed.

## NOT verified (read first)
- Every Postgres statement (advisory-lock signatures, PUBLIC defaults, `aclexplode`, `proacl`/`datacl`, `pg_has_role`, `rolcanlogin`, `datdba`, temp-function lookup) is UNVERIFIED: nothing was run on Postgres. They are from the manual, reviewers or my reading.
- Build, host and signing behaviour (detached signature, CODEOWNERS, branch rules) is UNVERIFIED.
- The temporary-function claim (X-6.5 row) is now stated as WITHDRAWN as a fact and UNVERIFIED.
- Day figures in new Decisions 26 to 29 are assistant judgement, not measured.
- I did not re-read every History paragraph; only the places named in the findings.
- Reviewer words were treated as unverified; source lines were re-read: `chain.py:120` and `migrate.py:314` are the only lock calls (one-number xact form); `checkpoint()` calls none; `effective_problems` runs only for the named logins (`migrate.py:298-303`).

## Findings
| Finding | Result |
|---|---|
| Design M1 | Criterion (9) allowlist rewritten: only `pg_advisory_xact_lock(bigint)` goes back, to the migration owner and the audit-appending logins; `signer` off from the start; check asserts the exact signature set per login. Decision 9b Ask and plain paragraph 9 agree. |
| Design M2 | Criterion (9) refuses while an undeclared login-capable role exists (`rolcanlogin`, database owner named); stored result has one writer (migration owner), commit, grant-map hash, logins run, mode answers. |
| Design M3 | EVIDENCE BINDING added: detached signature over (commit or tree hash, criterion, result hash), public key pinned outside the repository, dedicated approval key; UNVERIFIED. New Decision 27. |
| Design M4 | 9a/9b: a "no" counts only with an existing bound note; mode recorded; yes->no needs a new note; mode B says setting plus note. |
| Design M5 | ACL queries named (`aclexplode`, NULL ACL = default incl. PUBLIC, `pg_has_role`), owner/superuser/db owner excluded, planted-gap test plants a direct grant for the agent login. "If yes" of 9a/9b marked UNVERIFIED. |
| Design notes (two) | Temp-function claim withdrawn; "If yes" outcomes marked UNVERIFIED. |
| Reader M1, M2, M6, M7, M8, M9 | Fixed in batches b1 and b2 (one Q1 statement; X-2 two-stage and one Decision 2 trigger; drain and step definitions; Decision 19 decimal-price answer format; fallback write path ordered after X-2; README pointers, header stamp, bare log names with folder, `/tmp` cites marked may be cleared). |
| Reader M3 | One range (1) to (9) and a table of which criteria a note can close, in criterion (8). |
| Reader M4 | New Decisions 26 (notes folder), 27 (binding), 28 (start-up refusal wanted), 29 (the "does not sign" setting and its size), each with a block, a table row and a paragraph. |
| Reader M5 | Counts now 33 answers (29 numbered + 9a/9b/23a/23b extra 2 + 5-K + Q1); table rows added for 26 to 29, Q1 and 5-K; plain summary item 11, "Twenty-two matter for today's code", answer order and Decision 1 "decide after" updated. History keeps old numbers and says so. |
| Citation M-1..M-4, SOFT | Fixed in b3: README cite 168, false "24 instead of 26" removed (24 + 6 = 30, 26 + 6 = 32 counted from patch text), A-1/A-2/A-4/A-5 and the line-136 bullet re-pointed to `patch-copies/A-01.patch`, hunk headers +1,64 / +1,123. |

## Where a reviewer was wrong
- Reader M9: bare log names do not resolve only in `flows-audit/reviews`; `fix-review13/15`, `fix-patchcopies1` and `review-*-r1..17` are in `reviews-of-core-patches/`. Text now names the folder.
- Citation review "24 instead of 26" discrepancy: false; my own earlier reading of it was also wrong and is withdrawn.

## Command output (from `handover/flows-audit`)
- `count_review.py`: rows 28; Major 4, Minor 13, Nit 11; PROPOSE FIX 25, DECLINE 3.
- `check_refs.py`: PASS 5176 references.
- `check_names.py`: PASS 655 rows.
- `check_secrets.py`: PASS 0 hits in 2032 files.
- `ruff format --check .`: 746 files already formatted.
