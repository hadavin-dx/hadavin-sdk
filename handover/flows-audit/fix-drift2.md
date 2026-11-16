# fix-drift2 (fixer, review reviews/drift-007-r2.md, 2026-11-16)
Failures and gaps first:
- NOT DONE: patches/REGENERATED-NOTE.md lines 11 and 24 still keep the broad sentence "A lead sent twice is processed once in this recording" open (B1 part). The file is not in my allowed list. Next step: its owner must rewrite both lines to the Q25-2/Q28-1 sentence and drop "the lead may reword (handled once)".
- Reviewer words were checked against files first. Reviewer line numbers were off by one in places (patch L44 has no stopwatch text; the stopwatch is on L45); content findings all held.
- Nothing ran in n8n; static edits only. N2 (F-012) fixed by rewording; no measurement exists.

Backups: scratchpad bak-drift2/ (patch F-003, F-004, REGENERATED-NOTE, FINDINGS, LEDGER-ROWS, CUT-LIST, EXCEPTIONS, lanes7/).

Fixes
- B1: patch scene 3 caption and closing card now exactly "In this recording, the same lead ID sent twice gave one e-mail message in the intake mailbox."; no CRM-row claim; no broad "processed once" sentence; "receiving mailbox" renamed "intake mailbox" in the + lines; producer note on card wording rewritten (Q25-2, Q28-1); changelog line and open decision 1 use the same sentence.
- M1: scene 3 proof and rehearsal item 11: mailbox count after a stated wait (lead sets at rehearsal) plus the mf_leads row in frame; CRM count named as not proof.
- M2: all "stopwatch/overlay" text in + lines replaced by "the owner's own clock (no timer on screen)"; scene 4 has the cut rule (no takeover within 3 minutes: cut; lead sets final value after rehearsal); two context lines (sped-up rule, rehearsal item 10) turned into -/+ pairs (hunk counts unchanged).
- M3: scene 4: the lead stops and starts n8n with the stop and start scripts.
- M4: "deleted at clean-up" marked SUPERSEDED (no deletion promise, Q25-13a) in lanes7/N7-new-findings.md (3 places) and N7-verdicts.md (2 places); N7-7 marked SUPERSEDED by EXCEPTIONS.md; EXCEPTIONS paste labelled "AUDIT TEXT ONLY, NOT FOR THE VIDEO". LEDGER F-041 no longer says paste N7-7.
- M5: F-004 stale sentence replaced (patched statement 17 names no shipped lease; the 45 s/120 s facts kept as file facts).
- M6: F-003 no longer claims the patch marks the scene 4 caption "relayed from the lane3 test".
- M7: F-001 FINDINGS status now FIXED-UNVERIFIED (detail in text); F-013 status OPEN in both (ACCEPTED detail in the fix cell); LEDGER regenerated from FINDINGS, 45 rows, statuses 44 OPEN + 1 FIXED-UNVERIFIED, equal row for row.
- N1: CUT-LIST:17 -> :18 in LEDGER (regenerated from F-044 text; check) and N7-verdicts. N3: CUT-LIST ORDERS cites now have path handover/demo/ORDERS.md. N4: LEDGER header regenerated, cells full length. N5: label note at top of both N7 files (FINDINGS table is canonical). N6: raw output below.

Raw output (cd /home/user/hadavin-sdk)
```
$ sh handover/flows-audit/tools/check_patches.sh
PASS 4 patches
rc=0
```
(git apply --check is run inside it, so the hunk counts are exact.)
From handover/flows-audit: count_findings.py rc 0: rows 45 unique 45; Blocker 5/0/5, Major 7/0/7, Nit 1/32/33, all 13/32/45. check_secrets.py -I: PASS 0 hits in 1754 files, rc 0. check_refs.py: PASS 5147 references, rc 0.
