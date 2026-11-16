# Owner sheet v36 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: steps-edits/evidence-v36-independent/ (00-TABLE.md, 01-06). Recorded, not judged.
## Failures and deviations first
D1 plant P08 NOT caught: renaming the set phrase "contacts deleted <number>" to "contacts removed <number>" in facts-v36.py changes every built page together, and check-v36.py still reports 0 failures (no literal "contacts deleted" or "app passwords revoked" in check-v36.py or newchecks-v36.py; "run started" does have one). Class: a typed set phrase defined only in facts-v36.py is not pinned by a literal in the checks.
D2 v36-OPEN-FOR-LEAD.md line 134 has "08:00 IST the next day" with no UTC pair (nothing to compare).
D3 plants P10 (deadline 18:29 to 18:39) and P15 (output price 1500 to 1600) were stopped only by asserts in facts-v36.py (reported as C00), not by a content check.
## Results
Rebuild from source: exit 0, all 10 built files byte-identical to disk. check-v36.py: 0 failures. Word counts (own counter, whitespace-set counter, wc -w agree): sheet A 6,270, card 2,238, appendix 5,658, film 589, helper 956, A total 15,711 (cap 15,715, 4 under); B total 15,348 (sheet B 6,097); sheet A 16 under its 6,286 cap. UTC/IST: 198 pairs, 141 weekday-dates, 0 mismatches (16 Nov 2026 is a Monday). 20 hostile plants: 17 caught by a content check, 2 by facts asserts only, 1 missed (P08). Banned scan 0 hits (10 strings read at run time); secret-shaped 0 real hits (one base64-like match on the alphabet string at check-v36.py line 284); AKIAIOSFODNN7EXAMPLE 0 times.
## Not run
mut36.py (not touched), pytest, ruff, bandit, direct edits of built files, fuzzing; time/weekday regexes cover only the named formats.
