# fix-review55 (FIXER round 55, static only, security path)

Input: review-md-reader-r55.md. Backup: scratchpad REVIEW.before55. Only REVIEW.md and this file were written. All text is the audit's own proposals; nothing was built or run. Lines 5 and 77 unchanged (e6db355c, a3ab18f0). Line numbers are those of REVIEW.md after the edit (same line numbers as before; all edits are inside existing lines).

## Items
- Major 1 (file (ii) at case 4): FIXED. The four sentences (L631 WHO HANDS IN WHAT, L635 case 4 opening, L636 end of case 5, L660 Z17) and "4.1 to 4.9" (now "4.1 to 4.10", L635) rewritten; check 4.10 text and the Z2 sentence in L635 now say: absent file (ii) skipped, present file must match, matching file used for the Z2 re-run.
- Major 2 (log host root pin and Z2 digest): FIXED. Z1 part (2) (L628) and Z3 step (4) (L646) now say the deployer installs the new root pin on the log host by hand BEFORE any host starts the new (B); Z3 recovery-time sentence and Z3 test paragraph point to the new tests. Z2 (L645) has the sentence "WHO GIVES THE LOG HOST ITS PINNED DIGEST" (installed by hand by `log-admin`, advisory as part (8)(a)). Tests (ct), (cu).
- Minor 1 (entry types): FIXED. RECORD-RESET added to the type list (the log entry is renamed so "RESET" no longer means three things); "WHO MAY WRITE WHAT" added in L628 (two distinct keys for SEED, RECORD-RESET, OVERRIDE and first RELEASE entries; what the log host checks); Z6 (i) (L649) aligned to the eight types; L639 "RESET entry" replaced by "RECORD-RESET entry". Tests (cy), (cz), (da).
- Minor 2 (first release): FIXED. Both keys at a first release (case 2(ii), L633 and part (5) closing sentence, L639); signature count of entry 1 is now 2; what check 4.2 does at first release is stated. I also removed "4.8" from the checks that apply at a first release (there is no log entry to compare a hash with), a small inconsistency found while rewriting that sentence. Tests (cv) verifier, (cw) log host.
- Minor 3 (tests that could not yield their phrase): FIXED. A numbered ORDER OF THE LOG HOST'S CHECKS added in L628; (bm) now has a correct previous file, (bn) and (bp) use a tightening (B); (cl) and (cm) state present-but-wrong versus absent block (phrases and (ay), (bj)); (by) folded into (g) as a table input and kept as a pointer, like (k) and (ad) (the phrase "override counter is more than one above the log's" is dropped, L639 explains why); (bz) says the log is reachable and a record reset needs the log, new test (db).
- Minor 4 (Z2 new refused start-up file or variable): FIXED. It counts as LOOSENING unless (B) carries a signed counting-job result of the positive control (Z2, L645); test (dc). The other option (control in the signing procedure) is named and not chosen.
- Minor 5 (refused appends not alarmed): FIXED. Z6 (L649): refusal record on the log host, alarm check reads it (identity (viii) updated), alarm on every refusal with at most one message per cause, client id and hour (config value `refusal_alarm_minutes`, proposed 60, lead to confirm with OL-22). Test (dd).
- Minor 6 (weakness (vi)): FIXED in REVIEW.md (L642), rewritten from the reviewer's suggested text. NOT FIXED: the same flaw in fix-review54.md item 2 (frozen log of an earlier round, outside the files I may edit); REVIEW.md is the text that counts. Next step for the lead: leave fix-review54.md as history, or note the correction there.
- Minor 7 (wrong file (ii) at case 4): FIXED by refusal: 'previous file does not match the log at a current start'; (at) now covers the absent file only; new test (cx).

## New tests (11, (ct) to (dd)); one start, ten refusals
- (ct) log host, succession (B) g+1 before the pin is installed: [log host: signature does not verify]
- (cu) START, log host, same (B) after the pin is installed (one entry L+1, host starts under case 5)
- (cv) first release signed with one key: [first release needs the signatures of both keys]
- (cw) log host, entry 1 with one valid signature: [log host: first release needs both signatures]
- (cx) present file (ii) that does not match at H = L (table of two inputs, one cause): [previous file does not match the log at a current start]
- (cy) log host, OVERRIDE entry with one signature: [log host: override entry needs both signatures]
- (cz) log host, RECORD-RESET entry with one signature: [log host: record-reset entry needs both signatures]
- (da) log host, record-reset signatures as OVERRIDE and override signatures as RECORD-RESET (table, one cause): [log host: signed purpose label differs]
- (db) record reset with the log unreadable: [the log cannot be read or its chain does not verify]
- (dc) log host, new refused start-up file with no signed counting-job result: [log host: loosening needs both keys]
- (dd) log host, a refused append raises the alarm: [alarm: log host refused an append]
Changed tests (text only, letters unchanged): (g), (at), (bm), (bn), (bp), (by), (bz), (cl), (cm). The log-host conditional list was extended.

## Totals (all updated: L626, L644, L692, L829)
Z1 97 + 11 = 108 lettered; 96 refusals + 12 starts ((cu) added) = 108; distinct events 106 ((k)=(ad), (by)=(g)); 94 distinct refusals + 12. Z block 144 + 11 = 155; all 39 + 155 = 194; distinct 153 and 192. Letters: (a)-(z), (aa)-(az), (ba)-(bz), (ca)-(cz), (da)-(dd) = 26+26+26+26+4 = 108.

## Checks run (from handover/flows-audit)
- python check that the lettered list in the test line has 108 entries, complete and in order: True.
- line 5 sha256 prefix e6db355c; line 77 a3ab18f0.
- count_review.py: Major 4, Minor 13, Nit 11; PROPOSE FIX 25, DECLINE 3 (28 rows).
- 40-hex grep count: 0 (two 32-hex strings exist, unchanged from before: same two as in the backup).
- check_refs.py PASS 5190 references; check_names.py PASS 655 rows; check_secrets.py PASS 0 hits in 3011 files; check_counts.py PASS 52 files / 655 nodes; ruff format --check: 1136 files already formatted.

## Not checked
No design was run or built; the new text was read only against the sentences it touches. The new tests are the audit's wording; no phrase was run. Parts of REVIEW.md outside L626 to L660, L692 and L829 were not re-read in full.
