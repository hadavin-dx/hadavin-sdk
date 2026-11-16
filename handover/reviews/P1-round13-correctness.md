# P1 round 13, correctness review (ticket revision 14, commit 8b5d849)

Status: REPORTED, INCOMPLETE (saved by the lead session from the reviewer's hand-back, which is model output, not user authority). The reviewer says it was rebuilt after a context reset and did not finish every check. No verdict. Nothing was run; all traces are UNVERIFIED.
Target: `tickets/P1.md` revision 14 (336 lines). Reviewer: `egm:egm-codebase-details`. Did not open `reviews/`.

## Gaps stated by the reviewer
1. `studio-notes/amendments.md` not read (required read).
2. Redactor clause of the coverage sentence not checked against `guard/redact.py`.
3. v1.1 rows (25) not independently recounted; search-string uniqueness not checked for all 28 re-pointed mutants or the new P1a/P1b mutants.
4. Rows NB-P, `_checked` helper and the `names_equal` huge-second-argument trace not finished.

## MAJOR
**COR-R13-1 (lines 86, 109).** The ticket says every P1m mutant ends KILLED except "a failing tree kill is not caught". The batch-2 mutant "b2: a refused junit stops the run" is a declared CRASH: snapshot `tests/promoted_mutants.py` 1753-1759 gives crash type `ValueError`; the builder sets `allow_crash=bool(crash), crash_type=crash`; `tools/mutation_runner.py` line 290 accepts it only as `crash_ok = v is Verdict.CRASH and m.allow_crash and m.crash_type in first`. Fix: name both exceptions to the rule; require the moved mutants file to carry `allow_crash=True, crash_type="ValueError"` for that mutant, otherwise the judge reports an unexpected verdict.
(Lead check: the snapshot lines 1753-1759 and runner line 290 read as the reviewer says. Lead read, did not run.)

## NIT
- COR-R13-2 (line 274): "CLOSED, line 262" is a stale cite; line 262 is PENDING LEAD 47. Cite by item name.
- COR-R13-3 (lines 23, 231, 265): the claim that P2a cites P1 by item name only is false; P2a line 114 still says "`P1.md` line 18". (Lead check: confirmed by grep.) Correct the claim or have P2a change.

## Verified correct (by reading, UNVERIFIED by run)
Coverage sentence byte-identical at six places (7, 19, 47, 50, 220, 254); exact hex/base64 clause supported by `tools.py` (`_derived` 716, `_secret_forms` 744-759, `_scrub` 898, `_scrub_layers` 906-933); snapshot `textnorm.py` (181 lines), `_confusables.py` header and entries, `mutation_runner.py` (295), `testing/mutation.py` (105) cites; moved tests exist at cited lines; 28 + 21 mutant name lines; `_RETARGET` 1800/1812/1873; `runmap.py`, `defaults.py`, `ci.yml` cites; counts P1m 21 = 3+13+5, re-pointed 28, P1a new 14, P1b new 18, distinct 81, runs 109+k (k 0..14, max 123), public names 19, constants 3; cross-ticket cites in P2d (3, 30, 33, 34, 264, 266, 315, 334, 339), P4d (17, 150), P5a (21, 32); traces NB-1, NB-2, R12-LM, R12-LM-FOLD, R11-CYR, R11-GRK, Sigma row.
