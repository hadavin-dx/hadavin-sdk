# fix-review33: round 33 batch on `reviews-of-core-patches/REVIEW.md` (one fixer, security/money/redaction path, uncapped)

Edited only `REVIEW.md` and this log. Nothing run on Postgres or a host; every proposal in the new text is UNVERIFIED. No secret or personal handle copied. `patch-copies/` not touched.

## NOT verified (read first)
- Postgres, `ssh-keygen -Y verify`, `cryptography`, host and CI behaviour: not run. Source cites I used were opened: `audit/signer.py:45`, `store/postgres.py:494,499-503,523-530`, `0005_evidence.sql:12`, `store/migrate.py:57-63`, `runtime/tick.py:184-217`, `cli.py:383`. `tick.py:189` (reviewer) is inside the docstring of that step; I cited `184-217`.
- Whether `handover/` is published: not checked (CLAUDE.md says the repository is public and keeps private notes in `handover/`).
- I did not re-read the whole file after editing; I ran the five scripts below and greps for the old wording.
- `check_names.py` and `check_secrets.py` are not executable here (permission denied when called directly), so I ran them as `python3 -I tools/check_names.py` and `python3 -I tools/check_secrets.py`.

## Finding -> result (all reviewer words checked against the file and source; none contested)
| Finding | Result |
|---|---|
| B1 (verifier written by builder, reuses `verify_signature`) and F1 (same root) | FIXED. Decision 27 "WHO COMPUTES IT": separate program in its own repository, no import of `hadavin_sdk`, independent pinned signature tool, ONE NAMED PERSON writes or reviews it line by line, no builder or assistant session has write access (pull-request proposals only), hash pinned in release record (B) signed by the approval key, own negative tests (wrong A, wrong B, expired, replayed nonce, unsigned or lower-counter list, missing list, `.pth`/`sitecustomize`/`usercustomize`, `PYTHONPATH`), domain-separated encoding. The `verify_signature` reuse sentence is replaced by a refusal. "Until that person is named no signed note and no claimed-met evidence counts, and no criterion may be reported met through (8)" added to the hold sentence, Decision 27, criterion (8). Rows 27, 28, (8), Decision 27/28 "Who", criterion (8) text fixed. Hardware key: "a PURCHASE and needs the studio head's yes with numbers". The named person is part of the answer to Decision 27, not a new numbered decision. |
| M2 (revocation replay, stolen key, lifetime) | FIXED in Decision 27: minimum counter in (B), list may be signed by the NEXT key, maximum note lifetime (30 days proposal, head sets), negative tests incl. first start with no stored counter; key-set sentence covers a STOLEN key. |
| M3 (admission blocks stop and drain) | FIXED: ADMISSION BY PROCESS KIND (ACT processes may be refused; protect-only processes always start; operator STOP never gated, RESET may be) plus test; pointer in Decision 28. |
| M4 (install tree writable) | FIXED: read-only install tree or digest-pinned image with read-only root, re-check at restart and on a timer, negative test. |
| M5 (purge keyed on program-set times) | FIXED in X-5.7 (new round 32 paragraph) and criterion (6): database-set `created_at` on `tool_calls`, immutable insert-once time on `redaction_maps`, hold-list writer named (`holds` login, person's command), ceilings explained, two negative tests. Class check: sibling program-set times found were `tool_calls.created_at` and `redaction_maps.updated_at`; `tick_state` times were already covered by round 30 F4. |
| M6 (one writer claim; outbox and spool) | FIXED: Decision 4 reworded (refused INSERT plus recorded writer, not "one writer"), criterion (5) second test, spool open question answered by a proposal (sub-folder per writer, writer read by `fstat`). |
| M7 (heartbeat to a different person) | FIXED in the liveness paragraph (line 264) and Decision 25: alarm to the studio head's own phone, second delivery path, self-test by hand, wording "a different device or path". |
| M8 (client countersignature, core notes public) | Added as a proposal and a visible choice inside Decision 26 (no new numbered decision): sixth part for pilot or production notes (client countersignature or hash of signed e-mail, checked by the verifier, key pinned in (B)); core notes pointer plus hash only if the repository is public. Status: proposed by the audit; the head may change. |
| F2 (trigger dates) | FIXED: rows 27, 28, 29, Decisions 27, 28, 29 now say before the proposal under Decision 1 option 1, before the first pilot only under option 2; TIMING line lists 26, 27, 28, 29. |
| F3 (allowed-work list) | FIXED: two first dated actions added; start-up check bullet says design only until 27 and 28 are answered and the person is named. |
| F4 (item 26 placement) | FIXED: moved directly after item 25, before the "only if a patch is applied" heading. |
| F5 (Decision 29 in no wave) | FIXED: in wave 1 (plus the verifier written by the named person); wave 2 starts when 29 is built. |
| F6 (four vs five parts) | FIXED: parts listed ONCE under ACCEPTANCE NOTE (five, plus the sixth if the head says yes); lines of Decision 1, 26, the work list and 23b point there. Remaining "four parts" hits are the C-01 patch, unrelated. |
| F7 (estimates disagree) | FIXED: criterion (3) text, row 29 ("about 3 to 6 days, the only place this figure is stated"), hold sentence; Decision 27 no longer states 3 to 6 days. |
| F8 ("no hours estimated") | FIXED at the two table-intro lines. |
| F9 ("12 Major items") | FIXED at the three places: 11 present today, 12th (X-2) only if A-01 returns. |
| F10 (rule item numbers) | CHECKED against `.claude/rules/least-privilege-hard-rule.md` (1 one identity per function incl. audit writer, 2 least privilege and short-lived, 3 agents never hold approver or executor credentials): reviewer right. Fixed at criterion (5) and (8) in the acceptance-note paragraph. Class search of every "item N" cite of that rule: no other wrong one. |
| Smaller: "27 + 4 + 2" | Explained at line 113. |
| DEAD-MAN-CHECK.md citations | NEEDS PATCH-COPIES EDIT (not made): `patch-copies/DEAD-MAN-CHECK.md` must carry the heartbeat wording; it and `patch-copies/README.md` cite `../REVIEW.md:5` and `:67`. This batch added no line above line 67, so both cites still point at the same text (checked). Said in the file at line 264. |

## Numbers held (restated)
28 rows (Major 4, Minor 13, Nit 11; PROPOSE FIX 25, DECLINE 3), 33 answers (29 numbered decisions + 2 split halves + 5-K + Q1). No numbered decision added.

## Raw output (run from `handover/flows-audit`)
```
python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md
rows 28 [...C-1 ... X-6]
severity {'Nit': 11, 'Minor': 13, 'Major': 4}
decision {'DECLINE': 3, 'PROPOSE FIX': 25}
python3 -I tools/check_refs.py        -> PASS 5176 references
python3 -I tools/check_names.py       -> PASS 655 rows
python3 -I tools/check_secrets.py     -> PASS 0 hits in 2666 files
ruff format --check .                 -> 814 files already formatted
```

## Needs lead
- Name the verifier person and the builder session (hold sentence dates) are still the head's and lead's; the audit invents neither.
- `patch-copies` edit above; `handover/ledger.md` rows still missing (unchanged).
