Status: resolved (categorised; fixes NOT yet applied, package code untouched)
# Goldfish Annotated Review Report: P1b result review round 1
**Target:** package branch core/P1b-fixwip @ 0d843b4, ticket handover/tickets/P1.md. Reports: round1-design.md (D1-D14), round1-codedetails.md (C1-C16). Redaction path: no round cap. Run by the cloud session (Opus, egm-resolve). I am not the author of the package (a builder was); I did not contest anything for convenience.
Checked by me on the 0d843b4 worktree (py3.13): evidence.contains(decomposed text, precomposed value) = False; "password" is not found in canonical("pass"+U+093E+"word").casefold(). Both reviewer claims confirmed. Not checked: everything else below is the reviewers' reading.

| merged | ids | sev | category | decision |
|---|---|---|---|---|
| M1 | D1, C1, C16 | MAJOR | PROPOSE FIX | Confirmed false abstain (precomposed value vs decomposed evidence). ALLOW-side loosening claim (D1) not yet tested against old code: first run the grounded() fail-before on core/P1a. Fix: compose with NFC after canonical inside evidence.normalise/contains (exact comparison kept); keep per-char view only in replace_canonical; add tests: decomposed vs precomposed both ways, grounded() decomposed identifier. Add perf row for canonical at the cap and a fast path for unchanged runs (C16). |
| M2 | D2, C5 | MAJOR | NEEDS LEAD | Ticket rev 16 does not describe the shipped surface (16 keys, 33 names, 12 TEXTNORM_* constants, scan_holds/register_value etc., injection.py/runmap.py edits). Cloud cannot invent an authorisation. Ask the lead which orders (137/140) authorise it; I then append them to the ticket (append-only) or cut. Also rename tests asserting <=8 (C6) once the bound is settled. |
| M3 | D3 | MAJOR | NEEDS LEAD + PROPOSE FIX | CoverageRefused on every plain ASCII secret at registration under default strict is plausibly an over-refusal. Fix proposed: measure refusal rate on a made-up secret corpus first (fail-before number), then make strict apply only to shapes with no usable view. The default is a decision for the lead (false-abstain ceiling). |
| M4 | D4, C9 | MAJOR | PROPOSE FIX | Over-cap text becomes guard_unavailable on the injection path. Measure flag rate and cost with -s; scan the head of an over-cap text or chunk; document the ceiling. |
| M5 | D5, D6, C4, C15 | MAJOR | PROPOSE FIX | Evidence gaps: fail-before vs core/P1a not run; S_call/SK-5 not recorded; skip reason (-rs) missing; dblink baseline. Evidence runner re-run (separate agent) with -s, HADAVIN_PERF_LOG, -rs, new tests on P1a. Cloud already has a passing dblink re-run (evidence/dblink-rerun-2026-11-09). |
| M6 | C2, D12 | MAJOR | NEEDS LEAD | Redaction map (runmap.canonical/_views) and evidence still miss a secret hidden by Mc/Lm/Sk marks (confirmed) and scan_holds has no production caller. This is the P1d scope (single choke point). Not deferred silently: rule says fix. Proposal: P1b ships as the library and P1d wires runmap.redact_text to it; lead must record that P1d is a hard dependency with a date and that no client data flows before it lands. |
| M7 | C3 | MAJOR | PROPOSE FIX | Default insertion minimum 8 contradicts the CHANGELOG table (Greek 12, Cyrillic 10; Cyrillic 9 unmeasured). Set default to the largest measured minimum (12) or measure Armenian/Georgian; fix both comments. |
| M8 | D7 | MINOR | PROPOSE FIX | Per-thread cache dict or lock; to_thread test. |
| M9 | D8 | MINOR | PROPOSE FIX | Re-run with -rs; named skip. |
| M10 | D9 | MINOR | PROPOSE FIX | Add mutants: app.build skips require_pinned_unidata; evidence.py; cache thread. |
| M11 | D10 | MINOR | PROPOSE FIX | Restore P1a CHANGELOG text, append new entries. |
| M12 | D11 | MINOR | PROPOSE FIX | Move thresholds to defaults.py; attach the measurement data. |
| M13 | D13 | MINOR | PROPOSE FIX | scan_holds keyword-only arguments (public name change: lead aware via M2). |
| M14 | D14 | MINOR | PROPOSE FIX | Measure import time; lazy-build tables if significant. |
| M15 | C7, C8 | MINOR | PROPOSE FIX | Vacuous assertion `cn not in TABLE` -> `ord(cn) not in TABLE`; fix message; add real U+0301 test. |
| M16 | C10, C11 | MINOR | PROPOSE FIX | Add U+02BC/U+2032 etc. to _PUNCT or state limit; has_mixed_script treat Mc/Sk as word-joining (redaction-adjacent, so fix, with test). |
| M17 | C12 | MINOR | PROPOSE FIX | One meaning for "spelling variant"; rename "marks variant"/"pass". |
| M18 | C13, C14 | MINOR | PROPOSE FIX | Worst-case perf row second = A^31+B with comparison count; widen fuzz alphabet. |

Counts: PROPOSE FIX 15 groups (incl. M3 part), NEEDS LEAD 3 (M2, M3 default, M6), CONTEST 0, DECLINE 0. Nothing contested: reviewers' claims either confirmed by me or plausible by reading.
Next: lead answers M2/M3/M6; builder (Sonnet) fixes M1,M4,M5(evidence by separate runner),M7-M18 in one batch; fresh reviewers round 2; no round cap.
