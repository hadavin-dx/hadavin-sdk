# DOCS3 notes (style review 2 fixes of the root docs)

Branch wip/cloud-core-c/docs3 from origin/cloud/core-c c55dd4fbb. Not merged.

## Decisions
- Label rule: no result line on file means UNVERIFIED. K12, K80a (were FIXED) and K80b, K85 (were PINNED) are now OPEN with that reason; the
  last row of 2.10 reads "UNVERIFIED ... no result line". FIXED/PINNED return when a batch is recorded. 2.7 approval-message TESTED lines were
  relabelled UNVERIFIED too (no batch for them is listed in 2.10); revert if the lead knows the batch.
- Brand test: BANNED list is in tests/test_no_reference_material.py (not repeated here, the test scans this file too). The three root files have no hit. slack, bedrock_guardrail, PuTTY, ARN, rds.amazonaws.com are not on the list.
  Kept the config values slack and bedrock_guardrail (code requires them); reworded PuTTY and ARN lightly. Only hit in the repo:
  handover/BRIEF-PREAMBLE.md (lead's file).
- Decoded views: runmap.redact_text runs the generic patterns on `undo(text)` (percent, entity, \u, \u{}, %u, \x, \U, 3-digit octal, NFKC to
  fixed point, depth 8) among its views; bare redact() has only the JSON-unescaped and canonical views. README now says so; marked UNVERIFIED
  (read in code, no test run for the README line). Not verified: that every pattern runs on the decoded view.
- K26/K29 default (tighten by 2026-11-23 12:00 UTC) now also stated in README waiver line, which keeps the acceptance OPEN. No owner decision made.
- K50 source named as the team's measurement note of 2026-11-20 (working note, not shipped).
- MEASURED defined (direct call or recorded run; "here" = direct call at 2552bcc95). TESTED definition weakened (names where 2.0/section
  openings/2.10 give them).

## Not done / left on purpose
- Older CHANGELOG entries (from the P1a/P1b text-fold sections onward, ~line 290+) still hold P1a, P1b, G4, ORDER, finding ids; several are pinned
  by tests (e.g. "module has 20 public names", "P1b must refuse an empty view"). Only "Pin (p1a-015)" was changed to "Pin".
- Test file names with k5 or g3 codes are no longer cited in the Unreleased text (described by what they pin). Kept names without codes.
- Sentences over 30 words remain in older read-only-evidence entries (scrub entries ~100-111).
- Tables other than 2.10 not converted; unnumbered appendix heading kept so the #words-used-here anchor still works.
- Whole three pin-test files run in background; the -k selection of CHANGELOG pins passed (7).
