# Q20.5 patch text (inputs-patch-Q20-5.patch/.md), round 1, codebase-details, condensed copy, 2026-11-16
Reviewer had Read/Grep/Glob only: flows read from the SQL dump reviews-of-flows-audit/evidence-A2.md, not git objects. Not checked: real mf-form.json/mf-recovery.json bytes, mf-sub-crm-mail.json (mail_sent, lease renewal, claim_token), Stored node SQL, real patch run, byte equality of old lines, "v11 line 36", "run card row 8".
## Blocker
B1 Lease sentence X:2 off by one: Claim inserts attempts=1; ClaimStuck re-claims only attempts<3 and adds 1, so at most 2 re-pickups = 3 tries in total counting the first. Fix: "up to three tries in total, the first one included". Same wording error in cross-read/CLAIM-EVIDENCE-Q21.md:11.
## Major
M1 X:2 says duplicate "skipped however long you wait"; lead's Q21.2 (ORDERS:151) says a gap longer than the lease is not claimed. Skip holds only while the row exists (lead empties mf_leads at clean start, Q20.2). Use: skipped while the earlier record exists; waiting longer than the lease is not claimed. The .md must list this deviation for lead approval.
M2 "crash" too narrow: ClaimStuck keys on claimed_until<now and state, so a first run merely slower than 45 s is also re-claimed (recovery every 30 s, earliest pickup about 45-75 s). Unknown whether the sub-flow renews the lease or checks claim_token.
M3 Stale "archive" remains in scope sheet S:23 ("second signal inside the sends' own finally (archive, result.json, final print)"); .md Failures item 2 wrongly says no relevant hits.
## Nits
N1 hedge "no delete call" in the first clause. N2 S:9 hedge "kept in n8n's own database". N3 3b says lead starts/stops "the model program"; Q19.4 names only n8n scripts, source unfound. N4 scratch-apply claim uncheckable.
Verified OK: old lines/line numbers/hunk headers, no CR, patch matches Q19.1, Q19.3, Q19.4, Q20.3, decision 10; pointers I.5, J, appendix 8 exist in v12.
