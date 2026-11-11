# PR H ticket rev 3: author report (2026-11-11, 16:54 to about 17:30 UTC = 22:24 to 23:00 IST)

Author of the ticket (egm draft step). This is not a review; fresh reviewers judge rev 3. Nothing was committed or pushed by me (the lead's "state: sync" commits picked up my files while I worked).

## Still open or unverified (read first)

1. **Standards text not read:** unicode.org and ecma-international.org gave no answer (`handover/evidence/PRH-plan/r3/hosts-check.out`: 000). The Unicode licence text, ECMA-48 clause numbers and CWE names stay "from memory". This needs the owner or a third party: questions-for-lead, "PR H ticket rev 3", item 1. The build does not wait for it.
2. **The rev-3 rules are proven only on reference scripts and on one-line changes of my own prototype**, never as built code: the W0 span rule, the `_scrub` rule, the step-6 refusal, dropping the joined-reading views, and the compiled ignorable class. My prototype is not independent evidence.
3. **Cost numbers are composed estimates** measured on main with the cost-relevant pieces swapped in, under load 4.6 to 5.7 with all three heavy slots busy. There is no end-to-end timing of the rev-3 design.
4. **Worst shape W:** estimated 4.21 s CPU at the cap (budget 6 s). A machine about 1.4 times slower refuses it. This is stated as an availability change and is not fixed (lead question 4).
5. **`stransi` 0.3.0 was not judged:** my adapter called a wrong method and raised AttributeError on every row (my slip). pyte and ansi2txt were judged on metadata only. The rung verdict does not rest on them.
6. **The 43-file run under the rev-3 prototype:** RUN2_LINE
7. **Mutant 37's killer is named but not proven.** Section 5.2 says what the builder does if it survives.
8. **Not run at all:** the full suite, ruff, bandit, the mutation runner, the Python 3.12 suite.
9. **My own slips this round:** the first oracle version was quadratic on an unended OSC (I fixed it before the recorded run); my checkpoint line stamped "17:10" was written at 17:01 (corrected in the note); the stransi adapter (item 5).

## Where each round-2 finding is answered

| Id | Answer in rev 3 | Ticket section | Evidence |
|---|---|---|---|
| D1 | `_scrub` finds on the joined copy and returns the SPACED copy with the gap-pattern mask, plus a backstop that withholds the result. Step 6 raises `RedactionError` and never returns the joined text. Promise 2 has no designed exception. | 3 (promise 2), W2 step 6, W3 `_scrub`, T12 D1 rows, mutants 23, 31, 42 | `r3/d1-scrub-{main,proto,rev3}.out` (the rev-2 prototype LEAKS the key in D1a and D1b; rev 3 masks all 8 rows); step-6 firings 0 in `check-nojoinedviews.out` and `repro-nojoinedviews.out` |
| D2 | New W0: one span rule in the sweep, `_keep_earlier_masks` and step 5. Contained spans are dropped; a partial-overlap chain gets ONE merged placeholder, so restore is exact. Main itself leaks. The PR H-c stub is updated, so it is no longer a prerequisite. | W0, T4, 5.2 mutants 27, 38-41, 7.8, 8.1 note | `r3/d2-overlap-main.out` |
| D3 | Measured: Hindi's 1.59x came from the prototype reader. Per-character canonical costs 1.04x and the compiled class 0.94x. Estimates are 1.00-1.04x on S1-S5. Gates G1-G3 are test assertions; G4 (1.25x) is evidence; a remedy rule is written. | 4.4, T9, acceptance 9 | `r3/cost-r3-main.out` |
| D4 | Joined-reading views dropped: max 10 passes. W is 4.21 s at the cap, against 7.61 s for 18 passes. 0 verdict changes over the author's checks. | 3, W2 pseudo-code, 4.4 | `r3/cost-r3-main.out`, `r3/check-diff.txt`, `r3/repro-diff.txt` (both empty) |
| D5 | Refusal stated; T9 uses 300 distinct CUT values | 3, T9 | - |
| D6 | ` ?` only between two word characters of the value, so there is one way to match | W2 step 5, T9, mutant 43 | - |
| D7 | PyPI researched. `regex` 2026.9.29 equals the pinned file (4,174), so the ignorable table is CUT-TO-CONFIG+GLUE. strip-ansi matches 1 of 36 rows; pyte is LGPL and a terminal emulator; the reader stays KEEP-CODE. Policy rung, generator, oracle, `_scrub` and W0 rows added. | 4 rung table | `r3/rung3-pypi-metadata.out`, `r3/rung3-compare.out` |
| D8 | Kept: one definition of "ignorable" is the class fix; behaviour changes are in the CHANGELOG list | 6.1 CHANGELOG rules | - |
| D9 | `--from-ucd` dropped; equality test gated by `unidata_version`, failing when `HADAVIN_REQUIRE_PINNED_UNIDATA=1` | W6 | `r3/oracle-*.out` |
| D10 | Definitions added | 1 | - |
| M1 | Confirmed on main (tools.py:786-791 calls `_decoded`). `_first_decoded` is EDITED to `runmap.undo(char)[:1]`. | W3, mutant 33 | main source |
| M2 | Complete state table (every state and terminator, ESC inside a string, line end, end of text); `strip_sequences` scope defined; reference oracle | 4.1, T10 | `r3/scripts/hidden_ref_oracle.py`, `r3/oracle-*.out` (48 rows PASS, linear, 0 of 20,000 property failures, 3.13.18 and 3.12.3) |
| M3 | Source files exist on `core/cloud-handover`; absolute paths and an extraction rule given | T5 | - |
| M4 | File/function table, `test_mf_` naming rule, a killer for all 43 mutants. Old mutant 35 was equivalent and is replaced. 36 is killed via a stand-in. | 5, 5.2 | - |
| M5 | S1-S5 exact lines; Hindi 0.99x estimate; remedy rule | 4.4 | `r3/cost-r3-main.out` |
| M6 | Literal commands: worktree, locked sync, `uv run --no-sync`, `heavy.sh` with redirects outside, main run, Postgres | 6.0 | - |
| M7 | WP0-WP4 (7 packages incl. 2a/2b/2c), each one commit, each green on its own; stop rule hands over a patch file, never a red commit | 6.1, 6.2 | - |
| M8 | Escapes-only rule; `RANGE_FILE_SHA256` name; scan_repo and gitleaks after every package; the ticket's own 12 invisible literals rewritten | 1 Notation, 6.1 | `r3/m8-gitleaks.out` |
| M9 | Both range lists written out in section 1 and in the oracle | 1, oracle | `r3/oracle-*.out` |
| m1-m9, nits | One line each | 8.6 | - |

## What I ran (all from `/home/user/build/prh-author/main` at 2a8c2aac unless named)

| Command | Exit code | Output |
|---|---|---|
| `python -I r3/scripts/hidden_ref_oracle.py <perl file>` on 3.13.18 and on `/usr/bin/python3.12` | 0, 0 | `r3/oracle-python.out`, `r3/oracle-python3.12.out` |
| `python -I r3/scripts/probe_d2_overlap.py` | 0 | `r3/d2-overlap-main.out` |
| `python r3/scripts/probe_d1_scrub.py main`, `proto`, `rev3` | 0, 0, 0 | `r3/d1-scrub-*.out` |
| `python r3/scripts/run_without_joined_views.py errata/check2.py` and `... errata/repro.py protofixes` | 0, 0 | `r3/check-nojoinedviews.out`, `r3/repro-nojoinedviews.out`; diffs empty |
| `python -I r3/scripts/cost_r3.py r3/scripts` | 0 | `r3/cost-r3-main.out` |
| `heavy.sh ... pytest -q -p plug_r3 ... 43 files` (run 1) | 0, but INCOMPLETE (no summary, 6,978 results of about 7,506) | `r3/targeted-r3-probe.log`, `r3/step6-count.txt` (0 lines) |
| the same with `-v` (run 2) | RUN2_RC | `r3/targeted-r3-probe-run2.log`, `r3/step6-count-run2.txt` |
| `uv run --no-project --with regex==2026.9.29 --with strip-ansi==0.1.1 --with stransi==0.3.0 python -I r3/scripts/rung3_compare.py ...` (throwaway cache, deleted) | 0 | `r3/rung3-compare.out` |
| PyPI JSON fetch for 5 packages | 200 each | `r3/rung3-pypi-metadata.out` |
| `gitleaks dir` on two scratch files | 1 (one finding), then 0 | `r3/m8-gitleaks.out` |
| `curl -m 10` to the 3 standards URLs and PyPI | 000, 000, 000, 200 | `r3/hosts-check.out` |

## Files changed

- `handover/tickets/PRH-strip-hidden-controls-at-the-choke-point.md` (rev 3)
- `handover/tickets/PRH-c-map-entries-hygiene.md` (rev-3 section: no longer a prerequisite)
- `handover/questions-for-lead.md` (PR H rev 3 items 1-5)
- `handover/evidence/PRH-plan/r3/` (evidence and scripts)
- `handover/reviews/PRH/author-rev3-report.md` (this file)

PRH-b was not changed.

R-numbers used: R447/R448 (rung table), R449 (no stage names introduced), R371 (no shared cache: the probes use throwaway caches).

Process hygiene: background jobs `bcexr6hqi` (run 1, finished) and `b7hhf17pg` (run 2, RUN2_STATE). The temporary uv cache was deleted; no other process was started.
