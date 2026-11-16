# fix-patchcopies27 (twenty-fifth fixer pass on patch-copies/README.md and DEAD-MAN-CHECK.md; answers patch-copies-reader-r24.md and the open items of r20b, r20c, r12)
Security path, no round cap. Static work; made-up data; nothing applied to a real repository; no secret written; hashes shortened to 16 characters. Report time: 2026-11-16 about 20:40 UTC (02:10 IST on 2026-11-17) by the machine clock. EGM: the lead runs the review of this result; the fixer did not review itself.

## Not verified, not run, or open (first)
1. The recipe as one piece, real `uv` and real pytest were NOT run. The three functions `verdict_run`, `proof` and `final` WERE run exactly as written in the README, on a scratch clone made from `git archive b4cce5b` with the real patch files applied, with made-up pytest logs and a fake `E`.
2. The failing write of the second line of `verdict.stamp` inside `verdict_run` was not run in place (this machine runs as root, so a read-only file does not fail). The same branch was run alone in a scratch shell.
3. The names in `pwant` against a real pytest summary, a git older than 2.43.0 and macOS: still UNVERIFIED.
4. Slip in the report of the previous pass: `fix-patchcopies26.md` says "about 20:35 UTC", but the machine clock read 20:27 UTC when this pass started; that report time was an estimate that ran ahead of the clock. The README now says "by the clock of the machine".
5. `DEAD-MAN-CHECK.md` was NOT changed in this pass: every DMC item of the brief was already fixed (table below). Not edited, so no new history line there.
6. LEAD DECIDES (unchanged, from fix 26): hard minimum git version for `git patch-id --verbatim`; the lead, before the first real run, no later than 20:00Z (01:30 IST) on 2026-11-17. Also open, needs a frozen-patch edit: the missing self-hosted price test and the wording RV-A1 (marked EXCEPTION in the README; next step: the lead unfreezes the patch copy or the studio head decides; not done here because no `.patch` file may change).

## r24 findings (all six fixed in README.md)
| Finding | Done | Evidence |
|---|---|---|
| M1 proof refused `.hypothesis/` that `ut` allows | `grep -v '^\.hypothesis/'` added to the `st=` line of `proof` | scratch run: `.hypothesis/` in the unpatched clone, `PROOF OK` |
| M2 stamp taken after the clauses | `s0=$(sg "$W/patched")` after `ok=1`; the stamp write requires `$stamp = $s0` | scratch run with a fake `sg` that changes on its second call: `(stamp) FAILED`, NOT PASSED, exit 1 |
| M3 unpatched clone not in the stamp; function list omitted `hf`, `vs_ok` | new function `ug`; line 3 of `proof.txt` `unpatched <fingerprint>`; `final` compares it again; the list of needed functions names `hf` and `vs_ok`; the Pass-rule text says lines 2 and 3 | scratch run: edit of the unpatched clone after the proof gives `FINAL: NOT PASSED` |
| M4 `final` message "run verdict and proof first" | now points to the STOP or `PROOF FAILED` line that `proof` printed | text |
| M5 wording | PASSED row: "cannot occur at commit `b4cce5b`" and "NOT a merge clearance"; "no printed line starts with (f)" at both places that said "print clause (f)"; part (7) says a missing `FINAL:` line is not a fourth name | text |
| M6 stamp write failure shows PASSED, exit 0 | the `>>` failure sets `ok=0`, removes `verdict.txt` and `verdict.stamp`, prints `PART 1 OF 2 ... NOT PASSED`; the screen line is printed only when `verdict.txt` exists | branch run alone in a scratch shell (item 2 above) |

## Items of r20b, r20c, r12 (each checked in the current text first)
| Item | Status | Where / what |
|---|---|---|
| r20b M1 exit-code forward pointer, 70-77 / 129 / 130 / 143 | already fixed (pass 24) | DMC line 3 names 1, 70 to 77, 129 to 143 and "128 plus a signal", points to the table |
| r20b M2 proof compares counts only | already fixed | scope bracket says "proof failures compared by count and by test name, not by reason"; `pcheck` compares names |
| r20b M3 definitions before cleanup | already fixed | helper block right after the first block, part (4) |
| r20b m1 DMC N = 5 | already fixed | DMC rows D7, D9 and item 2 say "5 run periods" |
| r20b m2 gates cd | already fixed | gates run in subshells (history, pass 21) |
| r20b m5 fd 9 | already fixed | DMC lines 167-180: `9>&-` on lib, send_alert, send_ok, read_deadman_secret, psql |
| r20b m6 unlabelled inline spans | already fixed | DMC pg_hba and password-file lines say "content of a file, NOT a shell line" |
| r20b m9 C one of two names | already fixed | `verdict_run`, `proof`, `final` all check `C` |
| r20c M1 long paragraph | FIXED now | the 300-word paragraph above `verdict` is four short points; history is in the last section |
| r20c M2 3-character rule | FIXED now | stated in part (4) and in the failure-report paragraph (the `scrub` comment already said it); a name of 1 or 2 characters is replaced as a whole word, an empty value or a short home path is skipped with a WARNING |
| r20c m1 keep_logs second call | already fixed | refuses while `K` names a folder |
| r20c m2 cleanup refuses | already fixed | refuses unless logs kept, `final.txt` among the copies, or `DISCARD_LOGS=yes` for one call |
| r20c m5 verdict subshell wording | already fixed | the old sentence is only in the history block; the new points say what `verdict` leaves |
| r20c m7 "own block" | already fixed | no such wording in the instructions (only history) |
| r20c m8 hand-set W | already fixed | text matches `need_w` (tests only `setup.ok`) |
| r20c m9 "if C-01 returns" / "when A-01 returns" | FIXED now for the last one | "Major if A-01 returns" in the RV-X2 line reworded (REVIEW.md untouched; its own label stays there) |
| r20c m10 clock time, "newest commit" | FIXED now / already fixed | words table defines it once (80e9b09a7); the date paragraph and the new history entry carry UTC and IST |
| r20c m11 history says latest pass | FIXED now | date paragraph says twenty-fifth is the latest; pass 25 entry added |
| r12 M1-M6 and minors | already fixed in later passes (spot-checked: `-X`, `${CA:?}` guards, E guard, NOLOGIN, drift-check wording, row numbering text) | not re-read line by line; UNVERIFIED beyond the spot checks |
| outside range: DMC "the lead merges", README line 13 cloud question | already fixed | no "lead merges" text remains; the failure-report paragraph asks where the lead runs |

## What was run (raw results summarised; scratch under the session scratchpad `t27/`)
- `bash -n` on all 12 fenced blocks of README.md: no output (pass). DMC not changed.
- Fixture: archive of `b4cce5b` into two clones (the unpatched one cloned from the patched one so both have the same commit), `C-01-price-only.patch` and `A-01.patch` applied with `git apply`: 7 changed files.
- verdict: `(a) ok`, `(b) ok`, `(c) ok`, `(e) ok (7 changed files ...)`, `(d1) ok`, `(d2) ok`, exit 0. proof: `PROOF OK`, line 3 `unpatched ...`. final: `FINAL: VERDICT: ADDS NO NEW FAILURE ...`.
- Negative: edit of the unpatched clone after the proof gives `FINAL: NOT PASSED`; changing fingerprint gives `(stamp) FAILED`, `PART 1 OF 2 ... NOT PASSED`, exit 1.
- Not run: pytest, psql, uv, the full recipe.

## After the edits (last lines)
- `python3 -I tools/check_refs.py`: PASS 5190 references
- `check_names.py`: PASS 655 rows
- `check_secrets.py`: PASS 0 hits in 3014 files
- `check_counts.py`: PASS 52 files / 655 nodes
- `ruff format --check .`: 1139 files already formatted
- sha256 prefixes (16 chars) of the patch files, unchanged and equal to the README list: A-01 `64fdf315221fb9d6`, C-01-price-only `e7ff677e70d0c1fd`, C-01 `ca4982ebb9daef2d`.
- REVIEW.md not edited (its line 5 and 77 quotes unchanged). Not committed, not pushed.
- Files changed: `patch-copies/README.md`, this log. Backups of the two docs before editing: scratchpad `README.bak27`, `DMC.bak27`.
