<!-- full hand-back report of sub-agent a02f43ab, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PR H ticket ERRATA rev 2: report (ticket author; I have not judged my own work, and the ticket is not claimed READY). Real clock: about 16:20 to 16:47 UTC (21:50 to 22:17 IST).

FAILED OR NOT CHECKED (read first)
- I did not run: the full suite, ruff, bandit, gitleaks on the repo, the mutation runner, perf tests, or the Python 3.12 tests. Every result below comes from my own throwaway prototype (monkeypatches on clean main 2a8c2aac). None of it is independent evidence.
- I made three slips in the prototype during this pass. All three are now written into the design text:
  - The new "no created shapes" check ran a Unicode normalisation (NFKC) over the whole text before the size checks. Three cap tests failed (test_k5_fixes2/3). Fixed: the check now returns at once when nothing was removed.
  - The same check did not run inside the decoding rounds, so input F1e still forged a placeholder on safe_head and plain redact_text. Fixed: the rule now runs inside `undo`.
  - I overwrote that first cost output file. The two lines that matter are quoted in ticket W2.
- M2c (`&#6&#27;[0m5;KIA...`) still shows LEAKED in the check script. I judged it "not a key spelling": Python's entity decoder reads `&#6` as U+0006, so no reading spells the key. A reviewer may disagree.
- The cost limit "plain shapes at most 1.25 times main" is not shown by any run. The prototype measured 1.34 times on plain ASCII (single runs, machine load about 4). The design's compiled fast path is meant to close the gap; nothing proves it yet.
- I did not show that the `_keep_earlier_masks` ordering bug triggers on main itself.
- No commits by me. The lead's sync script had already committed earlier versions of my handover files (commit fa6cfb04). Nothing was pushed.

WHAT I DID, WITH EVIDENCE (raw files in handover/evidence/PRH-plan/, index in its README.md, scripts in its scripts/ folder)

1. Case 790 diagnosed (c790.out, c790d.out).
   - The leak needs no junk. Reduced input: `passw<i> </i>d=` + PART1 + `\U0000000b` + PART2 on channel.clean.
   - Cause: `_keep_earlier_masks` puts back earlier masks in list order. A shorter value's escaped spelling (the last 9 characters of PART1) is applied before the longer value's joined spelling, cuts it, and PART2 survives.
   - Bug class: overlapping known values replaced in list order instead of longest first.
   - Design answer: sort the pairs longest spelling first, at the choke point (W2).
   - Results: the round-12 fuzz file under the prototype goes from 1 failed to 5 passed. The sort alone on main also gives 5 passed. The 43 redaction-related test files: 7,505 passed, 1 skipped, rc 0 under the case-790 fix alone; the same counts under the final rev-2 prototype (targeted-proto-fix.log, targeted-proto-fixes.log). The 43 files include warden_port test_gate.py and test_gate_render.py.

2. The design reviewer's inputs, reproduced on main and on the prototype (repro-main/proto/protofix/protofixes.out, check-protofixes.out, cost-main/protofixes.out):

   | Item | Main | Rev-1 prototype | Status | Design answer |
   |---|---|---|---|---|
   | M1 (more than 256 values plus a hidden item in a word) | masked | LEAKED | reproduced | count only values that need the gap; over 256 refuse the text (InputTooLarge); values under 4 characters only as a whole word. Now MASKED |
   | M2a/M2b (`%4` + `%1b[0m` + `1KIA...`) | LEAKED | LEAKED | reproduced, a leak of main too | new decoded reading `undo(strip_hidden=True)` in `_views` and `tools._decoded`. Now MASKED |
   | M3 (runs of 2 or more items) | masked | masked | not reproduced as a leak; the wording was ambiguous | glue space decided per run, with a 10-row example table |
   | M4 (map clean-up drops a protecting entry) | — | 0 of 3,000 inputs | not reproduced | split out anyway |
   | M5 (card forges a placeholder) | forged | forged | reproduced on main | new rule for every caller: removing hidden items never creates a placeholder or marker. Card now shows `‹IPV4_1› and <IPV4_1>` |
   | F1a, F1b, F1c, F1e, F1g on safe_head and plain redact_text | all forge | not run | reproduced on main | same rule. None forges now |
   | M6 (grounding with U+FE0F / U+034F) | old behaviour | behaviour changed | reproduced | written into the contract (promises 4 and 5), test T11 |
   | `_first_decoded` skip guard | skips | broken (`""`) | reproduced | `_first_decoded` stays on the plain decode |
   | OSC row with U+009C | eats the rest of the text, output `'a '` | — | rev-1 row was wrong | corrected in 2.3 |

   - Generator axes added to T1: encoding layers, NFKC (full-width) carriers, run lengths 1 to 3, redact_value and redact_many, the size-cap seam.

3. Every readiness finding is answered: B1, B2, M1 to M9, m1 to m8, the "further ambiguous" points and the 7 builder decisions.
   - Line continuation: split out, as you recommended (stub `tickets/PRH-b-line-continuation-matching.md`). The map clean-up is also split out (`tickets/PRH-c-map-entries-hygiene.md`).
   - Order of steps for `redact_text` is now written as pseudo-code.
   - Unicode data file decided: `tests/fixtures/default_ignorable_perl5382_unicode1500.txt`, 17 ranges, 4,174 code points, SHA-256 b14f5d75…57f6, a copy in the evidence folder, `UNICODE_DATA_VERSION = "15.0.0"`. The from-memory rule matches the perl table on Python 3.12.3 AND 3.13.18 (di-312-313.out).
   - New mistake found in rev 1: it planned to pin that hash in `reference_material_sha256.txt`, which is a deny-list for course material. That would have made `tests/test_no_reference_material.py` fail on our own file. The hash is now pinned in the unit test.
   - Also in the ticket: a constants table built from parts; fixtures recorded from main, with a script, command and pass line; a stop rule; a who-runs-what table (heavy.sh 3 slots, 60-minute time boxes with 30-minute checkpoint notes, WP1 to WP4); acceptance items 1 to 12 as exact commands; Python 3.12 at /usr/bin/python3.12; gitleaks at /home/user/build/bin/gitleaks.
   - The machine profile names qsubmit.sh and the queue, but neither exists on this machine; the ticket uses heavy.sh instead.
   - The `_sanitise` second call site and the digest change at tools.py:1194-1197 are accepted with a reason and a test.
   - The canonical ripple (nfkc, undo, `_views`, evidence.py) is named and tested.
   - Wording fixed: "reading" (a version of the text) and "pass" (one run of all patterns) keep one meaning each; C0, C1, CSI, ST, CAN, SUB, DEL, nF/Fp/Fe/Fs are explained in plain words.
   - Q8b: the ticket now tells the Q8b builder to rerun its XPASS and fail-on-base checks after PR H merges.
   - Mutants are now 37. The pass count is now at most 18 (was 14), with the time-budget check before every pass.

4. Section 8.4 is the full table "finding id | answer | where in the ticket" for every Blocker, Major and Minor of both reviews. Items that need the owner or a third party are in handover/questions-for-lead.md (entry at about 16:40Z):
   - the merge order of PR H and Q8b;
   - ledger rows for PR H-b and PR H-c;
   - Unicode 15.1.0 data, the Unicode licence text, and the library research (proposed date 2026-11-18);
   - the judge / vendor screen / safe_head escaping decision (2026-11-18).

FILES CHANGED (all under handover/)
- tickets/PRH-strip-hidden-controls-at-the-choke-point.md (rewritten as rev 2, 631 lines, with the change list at the top)
- tickets/PRH-b-line-continuation-matching.md (new stub)
- tickets/PRH-c-map-entries-hygiene.md (new stub)
- questions-for-lead.md (entry appended)
- evidence/PRH-plan/: 21 raw outputs, scripts/, README.md

Also: /home/user/build/checkpoints/PRH-errata.md. Working files are in /home/user/build/prh-author/errata/.

STATE
- No processes left running.
- I recreated the detached worktree /home/user/build/prh-author/main (2a8c2aac), because the venv points at it. I kept it so the evidence scripts can be rerun; you can remove it with `git worktree remove`.
- R-numbers cited in the ticket: R447, R448.
- I did not measure my own token use.
- Plan review round 2 on Sonnet is the lead's step.
