# PD Part 6 batch 10 builder notes (branch wip/cloud-pd-banner-b7, base dd827d79)

## Facts first (what is not fully proven)
- The page and guard tests run in node/pytest only; no real browser. No full suite run (cloud limit); focused files only.
- Windows not run. Python 3.12 and 3.13 focused run: 314 passed each (test_banner_mutant_table, test_mode_banner, test_demo_only_guard); 164 passed in the 4 other files that mention the banner or guard.
- Freed-id reuse cannot be observed in a test; the seal now keeps every sealed part alive (weakref liveness pin), so a number cannot be reused while the seal exists. An id() comparison would be an equivalent mutant, so no row for it.
- copy.deepcopy of a built App is impossible (TypeError about a lock). App.__deepcopy__ now refuses it in words; tested (stub app and plain-parts app); copy.copy stays known; dataclasses.replace gives unconfirmed.
- Several new tests pass on dd827d79 and are named test_pin_*: see below.

## Changes per class
- A (seal): sealed value = (overridden, parts with references, banner services by value); one level of container entries (config systems/sources, registry agents/principals/chains/contracts/per-agent tools, toolbox specs/_fns); counters inside parts do not flip the banner (tick test); warn-once logging at WARNING with type name only.
- B (page): missing/null overridden unusable for demo/quiet; unconfirmed tone painted with the page's own tag, mode and text, names kept from overridden.
- C (masker): order BEARER, BASIC, URL, pairs (equals main for bearer 12+, basic 8+); limits stated; Part 6 does not call is_stand_in.
- F (guard): _entry_info parent-link check for loader, exempt files and copy marker; copy swap becomes SystemExit; chain-too-long rule name.
- Coordinator addendum: B12 killer now passes overridden=() (killed, see below); deepcopy handled honestly; pins renamed; table test now checks every killer name exists (R9A4 had a stale killer name, found only by running it, fixed); J1b needed a new killer (banner with real list or second line under unconfirmed tone) which is a pin.

## Fail-before (temp worktree dd827d79, new tests copied in, PYTHONPATH=old src; ids in /tmp/b10-ids.txt)
36 new or changed tests by AST at first count: 23 FAILED on old code (reasons seen: forged text painted, names lost, deleted tool spec not seen, host added not seen, replaced config source/contract/function not seen, no _WARNED/warn-once, page painted demo with overridden missing, bearer/basic token stayed visible, masker limit not stated, bare OSError, loader behind a link read through), 13 PASSED on old code. All 13 are renamed test_pin_* with a comment saying so. Plus the 28 pins from the evidence runner list (handover/evidence/PD-banner/dd827d79/fail-before-pins-passing-on-old.txt) all renamed test_pin_* (one of them, the reworded-banner test, now FAILS on old and keeps its name). The masker time tests pass on dd827d79 and FAIL on 07bfda12 (slow masker), shown by running them on that commit.
Honest limit: the warn-once tests fail on old only because _WARNED does not exist (AttributeError), not on the logged level itself; the level is killed by row R10A12.

## Mutants (python tests/banner_mutants.py; full table run in three slices, each under 8 minutes)
307 rows in total; slices 0-100 (99/100 then J1b fixed and re-run killed), 100-210 (110/110), 210-end (97/97), no shared first lines. New rows R10A1-A12, R10B1-B4, R10C1-C2, R10F1-F7 all killed or crash-as-pinned; R9A1 replaced by R10A1; R9D6 renamed; R9A4 killer name re-pointed (CRASH as pinned); B12 killed by its new killer.
