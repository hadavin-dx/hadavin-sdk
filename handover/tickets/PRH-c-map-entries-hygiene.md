# Ticket PR H-c (STUB, split out of PR H by ERRATA rev 2 on 2026-11-11): map entries that no placeholder in the output refers to

Status: stub written by the PR H ticket author (updated by PR H rev 3, see the section below). Not reviewed, not built. It needs its own EGM plan review before any build. Independent of PR H (a different bug class: what the run's map keeps, not hidden characters).

## Facts (main 2a8c2aac)
- In 530 of 7,066 generated inputs, the map that `redact_untrusted` returns holds an entry that no placeholder in the output refers to; in 386, one entry's value is contained in another entry's value (`/home/user/build/prh-author/scratch/fuzz.out`, author run, not independent). Cause: when a second reading of the text finds something new, its output replaces the first one (guard/runmap.py:517-518), but the entries the first reading added stay in the map.
- This was the lead's point 5 of the PR H addendum.

## Why it was split out of PR H
The PR H design review (round 1, finding M4) showed that the planned clean-up ("drop every entry this call added that its output does not refer to") can drop an entry that protects a LATER text: the run's map also masks known values in later texts (the sweep of known values), and `k1b/redaction.py:172-195` builds one map in pass 1 and relies on it being complete in pass 2. ERRATA rev 2 tried the design reviewer's scenario on 3,000 generated inputs with the author prototype and found no input where the clean-up changed a later text's verdict (`handover/evidence/PRH-plan/repro-protofixes.out`, line "M4 count"), but 3,000 generated inputs are not a proof, and the argument stands.

## Rev 3 of PR H (2026-11-11): the root condition no longer threatens a promise
The design reviewer of PR H round 2 (finding D2) named the "one entry's value inside another" condition above as the root of PR H's case 790. PR H rev 3 answers it inside PR H, not here: its work package W0 replaces every "put known values back one after another" loop (the redactor's sweep, `_keep_earlier_masks`, the gap replacement) by one span rule, so a value inside or overlapping another can no longer cut it (`handover/evidence/PRH-plan/r3/d2-overlap-main.out`: main leaks a piece on partial overlap; the rule masks all 7 rows). So this ticket is map hygiene only (what the map keeps), with NO dependency in either direction: PR H's promises do not wait for it, and it does not need PR H. If it is built after PR H, its property test runs on top of W0.

## What this ticket must decide
1. The rule: keep every entry a call saw (a value the run has seen stays registered for the whole run), and fix only what is wrong for the reader (for example: an entry whose value is a part of another entry's value must not make the output show a fragment).
2. Tests: "a value a call saw stays registered for the run" (a later text holding it is masked); the 530 / 386 counts as a property test with a pinned expectation; the k1b two-pass flow.

Proposed ledger row date: 2026-11-18.
