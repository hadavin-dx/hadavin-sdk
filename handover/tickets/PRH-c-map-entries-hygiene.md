# Ticket PR H-c (STUB, split out of PR H by ERRATA rev 2 on 2026-11-11): map entries that no placeholder in the output refers to

Status: stub written by the PR H ticket author. Not reviewed, not built. It needs its own EGM plan review before any build. Independent of PR H (a different bug class: what the run's map keeps, not hidden characters).

## Facts (main 2a8c2aac)
- In 530 of 7,066 generated inputs, the map that `redact_untrusted` returns holds an entry that no placeholder in the output refers to; in 386, one entry's value is contained in another entry's value (`/home/user/build/prh-author/scratch/fuzz.out`, author run, not independent). Cause: when a second reading of the text finds something new, its output replaces the first one (guard/runmap.py:517-518), but the entries the first reading added stay in the map.
- This was the lead's point 5 of the PR H addendum.

## Why it was split out of PR H
The PR H design review (round 1, finding M4) showed that the planned clean-up ("drop every entry this call added that its output does not refer to") can drop an entry that protects a LATER text: the run's map also masks known values in later texts (the sweep of known values), and `k1b/redaction.py:172-195` builds one map in pass 1 and relies on it being complete in pass 2. ERRATA rev 2 tried the design reviewer's scenario on 3,000 generated inputs with the author prototype and found no input where the clean-up changed a later text's verdict (`handover/evidence/PRH-plan/repro-protofixes.out`, line "M4 count"), but 3,000 generated inputs are not a proof, and the argument stands.

## What this ticket must decide
1. The rule: keep every entry a call saw (a value the run has seen stays registered for the whole run), and fix only what is wrong for the reader (for example: an entry whose value is a part of another entry's value must not make the output show a fragment).
2. Tests: "a value a call saw stays registered for the run" (a later text holding it is masked); the 530 / 386 counts as a property test with a pinned expectation; the k1b two-pass flow.

Proposed ledger row date: 2026-11-18.
