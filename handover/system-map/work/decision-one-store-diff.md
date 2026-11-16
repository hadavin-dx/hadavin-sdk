# Difference: DECISION-one-store.md (root copy) against inputs/DECISION-one-store.md (inputs copy)

Checked with `diff` and `git log --format='%h %ci' -- <path>`, 2026-11-16.

## Which copy is newer (by commit date only)
- Root copy: last commit e60d64595, 2026-11-16 12:16 +0530 = 06:46 UTC / 12:16 IST. It has 20 lines.
- Inputs copy: last commit 79720a66c, 2026-11-16 14:29 +0530 = 08:59 UTC / 14:29 IST. It has 28 lines.
- The inputs copy is newer by 2 h 13 min. (The root copy has an earlier commit, 444103193, at 10:30:58 UTC / 16:00 IST on the same date, which is the 10:30Z first version.)

## Every difference
1. Line 7 (the `mf_leads` row, last column "checked where"). The two say different things.
   - Root: "film-v5 and real-v5 flows; WP6 smoke P11".
   - Inputs: "real-v5 flows (film-v5 is not in this video, decision 1 of 2026-11-16); WP6 smoke P11".
   - Only the inputs copy says film-v5 is out of this video.
2. Lines 21 to 23 of the inputs copy exist only there: a heading "OWNER CONFIRMATION 2026-11-16 (executions)" and its paragraph. It says:
   - The owner approved saving successful production executions ON for the take only (made-up data), then deleting them and turning saving off at clean-up.
   - Three open corrections from the independent map review: (a) the decision is an aim, not a state, and more stores and files exist (spend ledger, stage.lock, stage.journal.lock, ledger lock, take lock, tag marker in HOME, n8n.pid); (b) `mf_leads` is in an `app` schema but `n8n_drive.py:40-41` reads an unqualified `mf_leads` as one PG_USER; (c) the read-only count role is not built.
3. Lines 25 to 28 of the inputs copy exist only there: a heading "CORRECTIONS 2026-11-16 (docs only ...)" with four points.
   - (a) Aim not state. The one store is Postgres, and n8n's own state lives in a separate database `n8n` owned by role `smk_n8n` for the re-smoke. `stage.journal` stays the one exception. The other stores and files that are not in Postgres are listed again.
   - (b) Executions ON for the take only, deleted at clean-up. The scope sheet now says the same.
   - (c) OPEN, code change needed (M-1): qualify `app.mf_leads` in code, or state the search_path choice. The read-only count role is not built, so the count is not yet an independent-credential check.
4. Everything else is identical. That includes lines 1 to 6, 8 to 20, and the whole "Not decided / UNVERIFIED" section.

## What matters for the take
- Stores: only the inputs copy lists the extra stores and files that are not in Postgres, and calls the decision an aim. The root copy still reads like a state.
- Desk store: both copies say identically that the desk SQLite and its portal are retired from the take. Nothing differs there.
- Line 7: the film-v5 wording differs (item 1).
- Line 15 (decision 2, desk retired): identical in both.
- "Decision 10 correction": neither copy has a decision numbered 10; each has 5 decisions. The nearest match is the "CORRECTED 10:35Z" n8n SQLite row on line 8, which is identical in both. The 2026-11-16 corrections in item 3 exist only in the inputs copy.
