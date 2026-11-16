# fix-review47 (round 47, edits to REVIEW.md only, static, no git)
Start about 19:33 UTC, done about 19:55 UTC. Backup: scratchpad r47/REVIEW.md.bak. Edit script: scratchpad r47/edit47.py (39 exact replacements, each asserted to match once).

## Gaps first
1. The brief says lines 5 and 77 must hash to prefix cf231d4e. Before I started they already printed e6db355c (line 5) and 7f8da2ce (line 77); after my edits they print the same two values. I did not touch them. The expected prefix cf231d4e now appears only in checkpoint-r46.md, fix-review44.md, fix-review46.md. Something changed those lines after round 46. LEAD DECIDES: confirm e6db355c / 7f8da2ce as the new baseline, or tell me what to restore.
2. The reader file was not in the stated folder; I read it at ../reviews/review-md-reader-r47a.md.
3. The reader file is condensed (one line per finding, "~15 Minors" while the brief says ~20); I matched each named item to REVIEW.md by text, not by the reader's line numbers (L314/306/310 for M2 do not match one-to-one: the plans-UPDATE text sits in lines 306, 314 and the agent row).
4. L331 (the agent-and-tick row continuation) really ended mid-sentence ("It must never approve, stop or reset spend"). I completed it from X-6.1 to X-6.3 and marked it LEAD DECIDES (confirm or replace the ending).
5. C-4 rating: I contested (kept Nit, added a reason: the negative-price hole is counted in C-3 and C-7). If the lead prefers Minor, counts become Minor 14 / Nit 10; that is the exact input needed.
6. Not run: no Postgres, no git apply, no tests. The M2 claim (INSERT ... ON CONFLICT DO UPDATE needs UPDATE right) is from the Postgres manual by my knowledge and is marked UNVERIFIED in the text. DEAD-MAN-CHECK.md copy changed after the md5 recorded in REVIEW.md (now md5 ff8452194427aa4a7a4fd4788f643cdb, 471 lines); its three open sentences (5b, 6b, 7) are still open in the copy.

## Finding -> change
| finding | verdict | change |
|---|---|---|
| M1 L185 vs L173/174 | confirmed | L185 now says RUN only for C-01, C-01-price-only, A-01 (batch 46 table); G5 and in-order apply are RECORDED, NOT RE-RUN |
| M2 plans UPDATE vs upsert | confirmed in source: store/postgres.py:293-294 and :204-216 (ON CONFLICT DO UPDATE) | shorter list of agent row now has plans UPDATE; removed from TO CONFIRM OR DROP; why-cell, X-6.9 and the negative-test warning changed: keep UPDATE until save_plan is a plain INSERT, positive test added |
| M3 G-1 BLOCK claim uncited | confirmed | added grep results: BLOCK only gate.py:63 (docstring) plus two PEM patterns; "G5" only comments/docstrings; dropped "no independent second detector" claim |
| L167 "run" vs recorded | confirmed | wording now RECORDED, only RUN rows re-run |
| L188/185 first-version evidence | confirmed | new FIRST-VERSION NOTE bullet; L188 says first-version test files |
| C-1 vs L189 UNVERIFIED | confirmed | "Run" replaced by "READ ... I did not run it; UNVERIFIED" |
| C-5 :27 vs :28 | confirmed by grep: copies line 27 (75-48, 54-27); first-version match :28, def :27 | cite rewritten |
| C-4 Nit vs C-3/C-7 | contested | rating reason added (see gap 5) |
| "item 4" twice | confirmed | glossary bullet; "rule item 4"; "edit-list step n" |
| A-3 clause | confirmed | deferral reason corrected (lead default, not this finding) |
| A-2 DONE | confirmed | STATUS DONE IN THE COPY |
| A-1 first-version | confirmed | tagged FIRST-VERSION WORDING |
| "no event lost" | confirmed | qualified to accidental rows (row and Reason) |
| A-6 event id vs X-5.5 seq | confirmed | log event_id neutralised as A-4, never body; seq for chain rows |
| test_p2_postgres :289/:296/:299 | confirmed by reading the test: three inserts, :290 is the migrate assert | X-6.3 wording corrected |
| X-6.4 test in X-5.5 | confirmed | moved to X-6.4 |
| L273 "not read" DEAD-MAN | confirmed stale | now points to the edit list |
| D-1 vs copy | confirmed (copy names audit_reconcile in instructions) | reworded with current lines :45-49, :53, :68 |
| D-3(4) stale | confirmed | marked STALE FOR THE COPY; D-3 status line added |
| edit-list md5 / ready to paste | confirmed; md5 had changed | new md5, commands, current line map, "not ready to paste" |
| X-5.7(c) vs purge INSERT | confirmed | purge row: outbox INSERT in every case, hold SELECT only under HOLD-1 |
| (iv) HOLD-2 / holds login | confirmed | (iii) and (iv) now say which choice they belong to |
| X-6.6a-e, T1, T2, Q1, Z6, Z12 undefined | confirmed | first-use glosses bullet in Labels |
| L331 mid-thought | confirmed | completed, LEAD DECIDES |
| G5 rebase checks | confirmed | five named checks (proposal, not run) |
| which files exist | confirmed | one WHICH FILES EXIST bullet |

## Checks (raw last lines, run from handover/flows-audit after the edits)
- ruff format --check . : 1020 files already formatted
- check_refs.py: PASS 5193 references
- check_names.py: PASS 655 rows
- check_secrets.py: PASS 0 hits in 2895 files
- check_counts.py: PASS 52 files / 655 nodes
- count_review.py: rows 28, Major 4 / Minor 13 / Nit 11, PROPOSE FIX 25 / DECLINE 3 (unchanged)
- sha256 line 5 e6db355c..., line 77 7f8da2ce... (same before and after)
