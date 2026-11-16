# Look-alike design, round 8, correctness review (draft 8)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Target: `designs/lookalike-leak.md` draft 8 (head `2ca11dd`). Reviewer: `egm:egm-codebase-details`, full fresh pass, read-only, no shell (nothing run). Did not open `reviews/`.

Verdict: no Blocker. Three Majors (F1-F3), eleven Nits. Counts and code facts are sound.

## Verified OK
- Hand recounts match: 46 LK ids in 42 table lines plus GOLD-1; 9 strict xfail always (+2 if NAME/ADDRESS stay out); 37 FR rows; 59 mutant names = 22 deleted + 37 live (35 in P2d-2, 2 in P2d-2b); constants 2 or 3; PL-LK 1-46 none missing; LKV 1-16 present, LKV-11 and LKV-13 withdrawn.
- Code citations checked against the snapshot (redact.py, runmap.py, tools.py, agent_loop.py, requests.py, channel.py, k1b/redaction.py, k1b/replay.py, evidence.py, capped.py, defaults.py, textnorm.py, _confusables.py, generator, tests). All hold apart from F8.
- Snapshot mechanics hold: `sweep` is a case-sensitive literal replace; stage 2 of `redact_text` adopts the canonical or `undo` view only if more placeholders are held; the caller's map is updated only after a successful pass; `_decoded_masks` is a precedent for `undo(original)` and the `\0seed` exclusion.
- Hand traces hold: count-form rule (hit when `s.count(k) > e`), restore of placeholders, LK-PH-FRAG, FR-2b, FR-36..38, LK-PH-UNDO, LK-ENT-VAL, LK-ERRMAP, LK-TAG a/b, M18b/M18c, FR-39/40, M54. Every mutant has a killer (exception: F12).
- PL-LK-42's correction is supported by code (`_sweep` ~1485-1500: upper/lower copies of 8-11 character secrets are sent; the search itself is `sweep` 1294-1333).
- Nothing relies on the cut P1 entity step (mentions at lines 2, 3, 8, 36, 38, 109, 133, 180 are statements of the cut). P1 rev 12 agrees on `isalnum`, T0-T3, `REFUSAL_HANDLERS` (three entries). P2d stale P1b lines 3, 30, 33, 34, 264, 266, 315, 334, 339 match by grep; line 71 plausibly correct.

## MAJOR
**F1. Order 15 is not applied or cited anywhere.** It corrects order 14(2) to "only plain copies" and keeps the case-folded sweep as LKV-2 with the trigger "before any pilot with real client data". PL-LK-42 is not marked answered; the LKV-2 trigger is not that wording; section 1(c) adds a full-width/zero-width clause beyond "only plain copies". Fix: apply order 15 verbatim, mark PL-LK-42 answered, align LKV-2 and section 1(c).

**F2. P1 line cites are stale against P1 rev 12 on disk, and "rev 11 / rev 12 being written" is stale.** Merge order: design 22, now 23. `scan_keyset(raw) -> frozenset[str]`: design 60 (and 58), now 56. RES-1: 67, now 63. PENDING LEAD 31: 274, now 249. `TEXTNORM_MAX_CHARS`: 84, now 43/44/80. Section 8(6) points the P1 author at the wrong lines (correct: 23, 63, 249). Fix: re-cite or cite by name.

**F3. The count form puts originals back before any size bound.** A model-written text with many placeholders of a very long original can blow up memory and CPU before the size rule or deadline applies. `e` is a sum of (placeholders put back) x (largest `count(k)` over that original's keys); the expansion has no pre-bound. FR-14 and FR-35 do not cover it. UNVERIFIED by run. Fix: bound the restored length (a multiple of `TEXTNORM_MAX_CHARS`) before restoring; add an FR row and a mutant.

## NIT
- F4: section 13 still carries draft-6 counts (43/39, 8-10 xfail, 31 FR, 32 live); real: 46/42, 9, 37, 37.
- F5: PL-LK-37 body still says LK-PH-NESTED is an xfail and cites LKV-13 (withdrawn).
- F6: LKV-11 is also withdrawn; every "withdrawn" note and count must say two.
- F7: LKV-9 carries two triggers; pick one.
- F8: cite drift: `_seeded` is channel.py 51-55 (not 54-57); test cites omit test_k5_round9.py lines 180 and 334; `_run_tool` range is 286-308 (not 290-312); PL-LK-42 labels `_sweep` as the search but it is `sweep` 1294-1333.
- F9: P2d stale-line list omits P1b lines 257, 304, 327, 329, 340 and the tier N hit at 339 (tier N also at 22, 264, 274, 335).
- F10: hook text says "tags and selectors"; P1 rev 12 says "non-emoji selectors".
- F11: missing row preconditions: LK-LOW and LK-TITLE need a mixed-case V; LK-FAKEPH needs V to start with a letter.
- F12: LK-NOCACHE's M39 killer is introspection only; state it or add an output assertion.
- F13 (UNVERIFIED): LK-PCT-PLAIN bare path expected "refused", but the lead's table says percent-encoded plain equals plain and is masked; by code reading the bare path leaks today; a run is needed.
- F14: the `texts` list parameter of `check_lookalike` is always one text; make it a `str` or say why it is a list.

## Unverified by the reviewer
The count of 177 MA entries with ASCII target (148 letters; reviewer's grep gave 235/232, inconclusive); draft 7 commit `2c60222`; all timings; P1b behaviour; round-7 resolve facts; absence of a retire-list file; callers of the card sites; F3 and F13 need runs.
