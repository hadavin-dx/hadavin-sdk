# Real-v5 edit list v7 (fix pass 2, builder), 2026-11-16
Not done / not verified (first):
- The swapped node was never run in n8n 2.46.6, and nothing ran on the laptop. 2.1b "2 minutes" is still a builder estimate.
- Section 10b paste ran only against a scratch Postgres 16 server (user postgres, db take_db, schema app); the take's database, schema, login and count-role names are unread (UNVERIFIED 15). Edit 27 is marked as a drafter addition beyond Q15.2; the lead may strike parts.
- Flow files are not on disk in the inputs: `CrmIdOk` expression, `mf-form.json:27/97`, `mf-recovery.json:26` were NOT re-read. The digits rule is sourced from `evidence-A4-tree-hits.tsv:995` (quoting `handover/demo/REPORT.md:4`), the stand-in's answer from a scratch copy of `crm_stub.py` (lines 3, 9, 33-43; not in the inputs). By that reading a whole-number id passes CrmIdOk; UNVERIFIED 14.
- Glue `fill_flows.py` / `drive.py` still unread (UNVERIFIED 13).
- My own slips this pass: first `\copy` attempt failed (psql does not substitute variables in `\copy`), fixed by `\o :out` plus `COPY ... TO STDOUT`; a first scratch server died because /tmp permissions were reset, rerun under /var/lib/postgresql/scratch7. Both servers stopped and the scratch dir removed; no process left.

Done, with evidence:
- plan-v7-real-v5-edits.md: 29 edits (28 + one new for the "about 70 paste files" count). Dry run `dryrun-v7.txt`: rc 0, header 29 = parsed 29, every OLD text once in the original and in the running copy, in order; 558 -> 651 lines. Input sha256 starts 67a0a195537de875 (unchanged after the run).
- Readiness 1+2 (10b): one `psql` call checks `current_database()` against the lead fill-in `TAKE_DB_NAME`, then in one transaction with the table locked counts, exports, compares the file line count, truncates, counts again, commits only at 0. n8n stopped first. Test output `clean-start-test-output.txt` (script `clean-start-test/`): wrong db stops with 4 rows left; mismatching export stops with 4 left; right db exports 4 rows (line-break key stays on one line), ends rc 0, 0 rows; a second session's insert waited and landed after the truncate.
- Readiness 3 / facts 1: step 8 gives no anchor (v11 sheet has no running numbers; v3 numbering 1-23 archived).
- Readiness 4: "made-up lead record" / "lead-record id" for data, "the lead" only for the Claude session, in edits 4, 23, 26, 27, 29.
- Facts 2: 10b marked drafter addition beyond Q15.2 (ORDERS.md:123); rehearsal vs take database reconciled in the text.
- Readiness 5: key claim fixed and tested: NULL refused, '' accepted once (last lines of clean-start-test-output.txt).
- Readiness 6: recipe uses `git -C $HD show 5fdc659d1:handover/demo/n8n-flows-film-v5/mf-sub-crm-mail.json`, names `$T/flows/mf-sub-crm-mail.json`; run on scratch copies: only the `url` line differs (`swap-test-recipe-check.txt`).
- Readiness 7 / facts 7: what the stand-in answers and that CrmIdOk takes it, stated as read, with UNVERIFIED 14.
- Readiness 8 / facts 4: negative run really run: `swap-test-negative.txt` (positive plus empty, missing line, non-loopback, userinfo trick, other port, two lines: all refused, file hash unchanged, hubspot count 1 = STOP signal). Script, input copies and re-run commands in `swap-test/` (`bash swap-test/run.sh`, `bash swap-test/recipe-check.sh`).
- Facts 3, 5, 6 and nits: GO-1/V5-README citation removed; whole-file hashes cited `evidence-A2.md:6-11`; verifier labels dropped; json-id-null claim dropped; exact match of CRM_URL; plan steps cited by name (step 1.2, section 2 row `crash holds`) in item 14; file counts 71 paste files / 77 files include `2.1b.sh`; INDEX.md line 1 label, line 2 hashes; empty `crm_id` rows and rehearsal-id sources named in 10b.
- Banned-vendor strings (BANNED tuple of tests/test_no_reference_material.py): 0 hits in every file of this folder.
