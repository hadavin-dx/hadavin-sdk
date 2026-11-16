# Fix log, batch 44 (fixer batch 44), 2026-11-16 18:41 UTC / 00:11 IST (2026-11-17) to 18:55 UTC / 00:25 IST

Only `REVIEW.md` in this folder was edited. No patch file and nothing in `patch-copies/` was touched. Nothing was committed, built or run against the code; every change is a proposal in text.

## What failed, what is uncertain, what was not checked (first)
- Reviewer line numbers do not match the file, so I matched findings by wording, not by line. A finding whose wording I could not find is not listed as fixed.
- NOT re-read after the last edit: the whole of REVIEW.md end to end by a fresh reader. The checks below are mechanical only. No fresh reviewer has read the batch 44 text.
- The test counts (Z block 71, grand total 110) are counted by hand, not by script.
- NOT done: the finer r40 nits that I could not match by wording after the edits are not individually listed here; a further reader round should look for them. This is not marked fixed.
- The `/tmp` folders exist now (listing at 18:41 UTC / 00:11 IST) but may be cleared; REVIEW.md says so and carries the date and the command.

## Per finding group
| Finding | Result | Where in REVIEW.md |
|---|---|---|
| r39 reader Z block (Z1 to Z17), r39 design B1 and M1-M16 design holes | FIXED in text (proposals): log rollback bound, authenticated override, stored+1 in the log, previous release record handed in and hash-checked, tightening as additions with byte-identical old tests, unpinned fields into the release record, issue-time and expiry bounds, revoked build digests, PROTECT-ONLY split, separate checker identity, hold-place / hold-lift split, drain provenance, missing identity rows, alarm sender default plus alternative plus test alarm, countersignature advisory, Decision 29 config, job key custody | section Z (lines about 560 to 600), key table, criteria table |
| r39 reader M2 (single key denial of service) | CONTESTED: the release key alone can already refuse every ACT start, so the new text adds no new power; said in the Z2 text | Z2 |
| r39 reader M3 (PROTECT-ONLY list location) | FIXED: the pinned code wins; a move between kinds is a new verifier hash | Z block |
| r39 reader M5 (alarm versus view) | FIXED: every alarm condition is a single-read log check on the log host | Z block |
| r40 M1 (`/tmp` contradiction) | FIXED: one fact, dated, with the command | Words list, `/tmp` paths bullet (line 26) |
| r40 M3 (scattered open questions) | FIXED: one list OL-1 to OL-24, each marked with the gate it holds | section ALL OPEN QUESTIONS; pointer in the Decisions intro |
| r40 M4 (true hold gate) | FIXED: stated in Decision 1 | Decision 1 |
| r40 minors/nits: header, HEAD at freeze, glossary, History, dangling `- (9)`, stray `(1)`, "names him", mixed time formats | FIXED | lines 3, 25, 651, 656, History batch 44 entry, time pairs |
| Open decisions only the studio head can make | NEEDS STUDIO HEAD: OL-1 to OL-24 (defaults written, marked "proposal, studio head to confirm") | OL list |
| Doers with no name | marked NOT NAMED YET and listed in the OL list | OL list |

## Commands and output (from `handover/flows-audit`)
- `python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md`: rows 28; Nit 11, Minor 13, Major 4; PROPOSE FIX 25, DECLINE 3.
- `sha256sum reviews-of-core-patches/patch-copies/*.patch` prefixes: 64fdf315 (A-01), e7ff677e (C-01-price-only), ca4982eb (C-01): unchanged.
- `tools/check_refs.py`: PASS 5192 references. `check_names.py`: PASS 655 rows. `check_secrets.py`: PASS 0 hits in 2840 files. `check_counts.py`: PASS 52 files / 655 nodes.
- `ruff format --check .`: 965 files already formatted.
- Lines 5 and 77 of REVIEW.md: sha256 of both lines equals the scratchpad backup (`cf231d4e...a3`): unchanged.
- HEAD at freeze: `dfe8715a8` (`git rev-parse --short HEAD`, 2026-11-16 18:51 UTC / 00:21 IST); it moves while other sessions work.
