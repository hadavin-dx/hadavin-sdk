# result-resolve-1: egm-resolve, result round 1 of max 2 (headless, auto-accept PROPOSE FIX)
Status: resolved. Targets: REVIEW.md, CORRECTIONS.md, LEDGER-ROWS.md. Inputs: result-review-R1..R4.md.
Method: every Blocker and Major in R1-R4 was matched to REVIEW.md, a CORRECTIONS entry and a ledger row (by reading the lists; no automated check beyond the ledger format check).
PROPOSE FIX (applied): R4 items M5-M10, B1 count wording and unsupported claims had no entry; added C-24 to C-27 and RF-021 to RF-024.
Covered already: R1 N-1..N-4, R2-1..R2-5, R3 RF-R3-1..8 (CORRECTIONS C-01, C-05..C-12, C-16..C-23; ledger RF-001..RF-017).
CONTEST: R4's claim that the CUT-LIST adds to 36 files. Evidence: the table sums to 40 files and 525 nodes (REVIEW.md s6).
ESCALATE to the lead: (1) R4 rated B1 and B2 Blocker by the wording standard; I kept Major (lead check lowered B1; B2 has no take effect): lead decides. (2) The shim call (C-18) depends on whether the take laptop has Docker. (3) The Majors M4, M5 and the 503 route are runtime questions.
DECLINE (Nit): R4 N1-N11, F-... case folding, generator docstring, Message-ID in alert text (listed in REVIEW.md as Nits).
Counts: 4 fixes added, 1 contested, 3 escalated, 1 group declined. Round cap: this is result round 1; no round 2 re-read by a fresh reviewer was run, so REVIEW.md is NOT re-read by a fresh reviewer (disclosed in the FINAL block).
