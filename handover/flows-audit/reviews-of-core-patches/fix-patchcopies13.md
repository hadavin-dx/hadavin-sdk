# Round 13 fix of patch-copies README.md and DEAD-MAN-CHECK.md (one fixer, security path)

Date 2026-11-16. Edited only `patch-copies/README.md` and `patch-copies/DEAD-MAN-CHECK.md`. Not edited: the three patch files, `../REVIEW.md`.

## Failures and uncertainty first
- Nothing in the recipe or the job script was RUN. All I ran: `bash -n` on every shell block and one-liner I touched (and the untouched blocks of both files), `sha256sum` of the three patch files, `git -c diff.context=3 -c diff.algorithm=default diff --no-index --no-ext-diff /dev/null /dev/null` (exit 0, shows only that git accepts the two option names), and the four checks in `tools/`.
- Two unavoidable unknowns are written as open questions for the lead, not invented: (1) which channel receives a failure report (README now has the section "Where to send a failure report"); (2) whether the lead runs in the cloud or on the laptop (already UNANSWERED in the words box; unchanged).
- Added `-c diff.context=3 -c diff.algorithm=default` to function `gd`: that is a code change to a recipe line; syntax checked with `bash -n` only, and I did not test that those two settings really change the patch-id. Other unlisted git settings could still cause a false "(e) FAILED" (fail safe); the text now says that instead of "your own git settings cannot change the patch-id".
- Reviewer statements about uv offline behaviour (M4) are not checked by me (no uv run); the text says UNVERIFIED.

## Finding to result
| Finding | Checked against the text | Result |
|---|---|---|
| M1 no destination for failure output | true: lines 4, 10, 153 said "send to the lead"; the lead is an AI session (words box) and no channel is written anywhere in README, ORDERS or STATUS I searched | New section "Where to send a failure report (UNANSWERED lead item)": interim route (the person who asked you; a session puts it in its report), open question for the lead, cleaning rules moved there, plus a warning that the last log line printed by `setup`, `run`, `proof` may hold a web address. All four "send ... to the lead" pointers (setup message, fetch failure, odd-green case, line 4) now point at that section. The lead question is not answered |
| M2 words before explained | true | README line 4 now says what the function names are and points to the words box; DEAD-MAN-CHECK line 5 explains "four-name form" and `audit_reconcile` (and the outbox) at first use; "decision table" is now named once: heading renamed to "Decisions that the fixer session may not make" (also fixes the "mine" vs "never says I/my" clash; nothing else cites the old heading, grep checked); "identity table" renamed "statement table (section The statements)" in both files (the one remaining "identity table" is a different table in `REVIEW.md`, row X-6.6) |
| M3 "only edit is EXTRA_ENV" vs other edits | true: P, SRC, C, PY lines say CHANGE THIS and macOS asks to change two `sha256sum` lines | One list "Allowed edits (the only three)": the first-line values, `EXTRA_ENV`, macOS `shasum -a 256` in two named lines. Lines 10 and 156 and the two macOS notes now point to it |
| M4 offline route misses Python | plausible and consistent with `E` (`UV_PYTHON_INSTALL_DIR` is an empty folder); not run | Text says offline also needs Python 3.13 on `PATH` or a warm uv Python folder copied into `$W/uv-python` (one-liner added, `bash -n` ok, NOT RUN); whether the uv cache holds interpreters is UNVERIFIED |
| M5 `-p` missing, password source, exit 2 ambiguity | true: DBPORT used in the one-liner but absent in the admin psql line and the no-password test | `-p "${DBPORT:?}"` added to both; DBPORT added to the variable line of the password block; one-liner text now says a password source must exist (else exit 2 "no password supplied", same code as unreachable); no-password test now has a positive control first (same line with the real password file: exit 0 and `1`), then the no-password run, and says to read the message too |
| M6 test (iii-b) can not fail as written | true: lines 126-127 of the job call `send_alert` only on the unhealthy branch | (iii-b) now requires an unhealthy condition (wrong `NAMES_EXPECTED` or tick stopped) and explains why; (iii-c) added for `send_ok` failure (exit 76); "two cases" became "three cases" |
| Minor: `OK|||5` in today's form | true | now `OK|||4` (`OK|||5` after A-01) |
| Minor: heading 102 omits twelfth pass | true | fixed |
| Minor: clause order (e),(f),(d) | true | (d) moved before (e); order now a, b, c, d, e, f |
| Minor: patch-id wording overstated | partly: see uncertainty | reworded and two settings added to `gd` |
| Minor: EXTRA_ENV example copies `$HTTPS_PROXY` | true | warning added on the line itself |
| Minor: run/verdict print last log line | true for `setup`/`run`/`proof` (`verdict` prints the pytest summary only) | covered by the cleaning rule |
| Date paragraph | n/a | thirteenth-pass sentence added saying what was and was not run |

## Raw outputs
```
sha256sum (equal to the listed values):
64fdf315221fb9d653fe8defc844aa438c39c56bc32c5a86c70d8aab67892095  A-01.patch
e7ff677e70d0c1fd61e9c4e2f1024c58fd35b83bc715abd3d0449202038dae01  C-01-price-only.patch
ca4982ebb9daef2d5c96e1538d2cdde5291d2d9a948c70553b5661a0a17fded0  C-01.patch
check_refs.py    PASS 5175 references
check_names.py   PASS 655 rows
check_secrets.py PASS 0 hits in 2703 files
ruff format --check .   851 files already formatted
bash -n: README recipe blocks (7 blocks) rc 0; DEAD-MAN-CHECK job script and password block rc 0;
  4 touched one-liners (offline cache, offline Python, one-liner with -w, no-password test) rc 0.
  (The sample-output and SQL blocks are not shell and were not checked.)
git -c diff.context=3 -c diff.algorithm=default diff --no-index --no-ext-diff /dev/null /dev/null: exit 0
```
Agents or shells started: none left running. Not committed.
