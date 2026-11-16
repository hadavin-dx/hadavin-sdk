# Resolve, hand-off v14 reviews (security round 3, readiness round 3). Hand-off v15.

Status words: FIXED (where), CONTESTED (evidence), OWNER-ONLY. Nothing here is "verified" beyond the evidence named. EGM resolve skill not invoked (not available to this agent).

## Security
| Id | Status | Where |
|---|---|---|
| M1 | FIXED | 5.6 (a) to (i); held-sql default and variant; pg_v15 run1/run2 (16.15) |
| M2 | OWNER-ONLY for L7, L9 (left open); FIXED for reader role spec (5.6(h)); role code UNVERIFIED (not built) | OPEN-FOR-LEAD |
| M3 | FIXED in text and runs; 16.15 only | raw-pg-v15-run1/2 |
| m1 | FIXED | WindowOnlyGate, 5.1, 5.3, section 6 C7/C8 |
| m2 | FIXED in text | 5.3 / 7.1 qualify allowlist |
| m3 | FIXED in text | OPEN-FOR-LEAD top; L14 |
| m4 | PARTLY: search_path, key guard comment and alarm text in 5.6; retention delete = L16 OWNER-ONLY | 5.6 |
| m5 | FIXED | pre-flight lists +Infinity, tested |
| m6 | FIXED | one number set |
| m7 | PARTLY: asked in text; no lead answer yet | 5.5 |
| m8 | FIXED in text | helper renamed in 7.1 |
| m9 | PARTLY: G-4(i) = L14, retention = L16; G-4(v) not asked separately (gap) | OPEN-FOR-LEAD |

## Readiness
M1 to M7 FIXED in text as in v15-CHANGES.md; none of M3, M4, M7 code exists, so the tests are planned. Minors: D5 not a gate FIXED; other-tracks title v15 FIXED; `gate4.sh` UNTESTED disclosed; run.py pointer-file note mentioned only (other lane); 5.9 extra cell, DB-1 depends column, E0-S1-3 label order, S-1 mutants and size, 16.15-only: NOT individually re-checked in this pass (UNVERIFIED).

## Citations and evidence
28 near-miss: widened (34 + 7 ranges). 55 MOVED flagged, 15 read and right, 40 unread (UNVERIFIED, next step: a reader reads them). 142 planned/evidence names labelled by rule. `fileguard.py`, `owner_gates.py` named as planned. 8 builder files: named per section 8 (not re-counted here, UNVERIFIED).

## Orders
L7, L9, L16, L17 OWNER-OPEN, not assumed. Reader = audit reader role. Q34 default file kept exact with its own negative test, applied only on an owner yes.
