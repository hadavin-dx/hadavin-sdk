# Citation review r28 of REVIEW.md lines 1-487

Checker: citation checker (read-only; static; nothing run except `count_review.py`, `git show`, `sed`, `grep`). Date 2026-11-16. Checkout HEAD at check time `3306e02aa`. `git diff --quiet 176a0cbe0 -- src tests pyproject.toml` returned rc 0. Object `b4cce5b` exists (`git show` worked). Scratch trees `/tmp/core-b4p`, `/tmp/core-b4m`, `/tmp/smfull`, `/tmp/ch` existed at check time and were read for the patched-copy cites.

Method: a script took every `file:line` and `file:a-b` cite and every `:NNN` follow-on in the comma lists of lines 1-487. I resolved each file to the source tree and printed the actual line next to the claim, then judged the claim against the line. About 550 cite occurrences, about 390 distinct. Cites that name a patched copy were read in `/tmp/core-b4p`. Cites for commit b4cce5b were read with `git show b4cce5b:...`.

## 1. MISMATCH rows (2)

| # | REVIEW.md line | Cite and claim | Actual source text | Fix needed |
|---|---|---|---|---|
| M1 | 67 (plain summary item 3) | `patch-copies/README.md`, "Pass rule" has clauses (a) to (d); "there is no clause (e), and an earlier line of this file that said '(a) to (e)' was wrong" | `patch-copies/README.md:188`: "**Pass rule.** Clauses (a) to (e) say ..."; clause (e) exists at `:192` ("(e) both clones are at `$SHA` ... the 7 files of the default pair") and is used at `:171`, `:174`, `:198`. Clause (d) is at `:193`. So the README, as it stands now, HAS a clause (e) and the earlier line was right. The review says the README "is still being edited", so the README may have changed since it was read. | Say (a) to (e), or re-read the README and cite only its section name. |
| M2 | 73 (plain summary item 9) and 323 (the 'Not checked' bullet; the same text is at line 323 as the second hit of the phrase) | "the query and rows 1, 4, 5 and 6 of the read-only identity ... were seen once on a throwaway Postgres" (cites `patch-copies/DEAD-MAN-CHECK.md:12-16` and `fix-patchcopies1.md` section 6) | `DEAD-MAN-CHECK.md:12`: "the query (with five names) and rows 1, 3, 4 and 5 of the identity table below were run ONCE ..."; `:14-15`: "rows 2, 6, 7 and 8 ... passes were static"; `:137`: "(rows 1, 3, 4 and 5 only: the first pass)". `fix-patchcopies1.md` section 6 (line 36 on) gives no row numbers (its line 7 only names the `deadman_reader` identity). So the row list should be 1, 3, 4 and 5, and row 6 was NOT run. | Replace "1, 4, 5 and 6" by "1, 3, 4 and 5" in both places. |

## 2. Counts (all checked)

| Claim | Check | Result |
|---|---|---|
| 28 rows: 4 Major, 13 Minor, 11 Nit | `python3 -I count_review.py REVIEW.md` printed `rows 28 [C-1..X-6]`, `severity {'Nit': 11, 'Minor': 13, 'Major': 4}` | MATCH |
| 25 PROPOSE FIX, 3 DECLINE | same script: `decision {'DECLINE': 3, 'PROPOSE FIX': 25}` | MATCH |
| 29 numbered decisions, 33 answers | Decision table lines 327-476 has rows 1-8, 9a, 9b, 10-22, 23a, 23b, 24-29, Q1, 5-K = 8+2+13+2+6+2 = 33 answers; numbers 1-29 = 29 numbered decisions | MATCH |
| 41+14 tests, 15 new, 70 | `heavy-test-lane/SUMMARY.md:21-22`: "9404 minus 9389 = 15 more passes. The 70 new and changed tests alone pass (5 + 10 + 41 + 14)"; 41+14 = 55; 55+15 = 70 | MATCH |
| 15 failed, 55 passed; 13 new tests (6 price + 2 ceiling + 5 A-01) + 2 others | `evidence-13.md:23-24` | MATCH |
| price-only: 24 cases; C-01.patch 26; A-01 6 functions; 24+6 = 30; 26+6 = 32 | `grep` of `+def test_` gives 4 (price-only), 6 (C-01), 6 (A-01); parametrise counts 6+1+16+1 = 24 read from the patch text. README `:10-11`, `:98`, `:112` say 24, 26, 30, 32 | MATCH (cases counted by reading, pytest not run) |
| README 9394 = 9364 + 30; 12 failed 18 passed (price-only) | `README.md:242`, `:246`, `:219` | MATCH |
| `C-01-price-only.patch` is 78 lines, hunks `@@ -362,6 +362,16 @@` and `@@ -0,0 +1,51 @@` | `wc -l` 78; grep of hunk headers (`:5`, `:27`) | MATCH |
| C-01.patch test hunk `+1,64` at `:48`; A-01.patch `+1,123` at `:124`; raise at `C-01.patch:27` | grep / sed | MATCH |
| +37 and +55 added lines; 53 and 74 lines with 16 and 19 blank | `evidence-13.md:105` says +55 and +37; `/tmp/core-b4p/tests/` files have 53 and 74 lines and 16 and 19 blank lines (`grep -c '^$'`) | MATCH |
| Guard tests alone: rc 0, "2 passed, 10551 deselected in 8.54s" | `heavy-test-lane/evidence-guards-after-fix.md` lines 2-3 and 23; lines 4-14 are the `git status --short` list | MATCH |
| pydantic pin 2.14.1 at `pyproject.toml:16`, also at b4cce5b and `/tmp/core-b4p` | all three read | MATCH |
| `evidence-pydantic-nan.md`: PART 1 at line 50, PART 2 at line 58; NaN, sNaN, Infinity, -Infinity refused; 0, -1, 0.0000001 accepted | `:51-57`, `:63-83` | MATCH |
| Lead decisions: line 1 quote, item 4 at line 5, item 11 at line 11 | `inputs/DECISIONS-2026-11-16.md` | MATCH |

## 3. Tally of cite checks

Distinct file:line cites resolved in lines 1-487: about 390. By occurrence about 550.

- MATCH: about 380 distinct cites (including all patched-copy cites in `/tmp/core-b4p`, all b4cce5b cites, all demo cites).
- MISMATCH: 2 claims (M1, M2 above). M2 counts as one claim cited twice.
- CANNOT-CHECK: 12 items, listed in section 4.

Notable MATCH checks (the ones most likely to be wrong and were not):
- `config.py:394` `if is_live(self.environment):`; `:393` `refused = []`; `:401` environment `raise`; `:68` `max_tokens: int = Field(gt=0)`; `:64` `class Route`; `:49-56` `Money`; `:378` `_cross_checks`; `:384-386`; `:157-160`; `:419-420` `is_prod` / `NOT_PROD`.
- b4cce5b: `config.py:59` max_tokens; `:365` `refused = []`; `pyproject.toml:16`. Patched copy: `config.py:365` (price check start), `:373` (raise "routes with a zero or negative price"), `:374` `refused = []`, `:382` environment raise; `defaults.py:104` `MAX_ROUTE_TOKENS = 200_000`; `tests/test_c01_route_limits.py:27`; patched `gate.py` `:45`, `:62`, `:66`, `:206`; patched `redact.py:948`; original `gate.py:42`, `:59`, `:63`, `:203`; `redact.py:947`.
- `audit/chain.py:232` `def reconcile`, `:244` the `DELETE FROM audit_outbox`, `:229` `_pending.append`, `:47` `_PG_LOCK`, `:117`, `:120`, `:123`, `:243`, `:295-317`; `local_dir.py:126-156`, `:143-147`, `:154`; `protocol.py:27`.
- `store/migrate.py:46-68` grant map, `:57` audit_entries `_APPEND`, `:58`, `:59` outbox `SELECT, INSERT, DELETE`, `:56` tick_state `_RW`, `:193` `effective_problems`, `:283-292`, `:286-288`.
- `runtime/agent_loop.py` `:768`, `:886`, `:901`, `:909`, `:845-867`, `:252`, `:817`; `runtime/tick.py` `:85`, `:59-60`, `:133`, `:162`, `:249-266`, `:315-324`; `app.py` `:62`, `:86-89`, `:146`, `:151-160`; `limits.py:43-52` (stop switches first, reset audits first).
- Demo: `askdata/config.py:61-70` and `:64`, `:87`, `:80-94`; `evalcli.py:70`, `:88`, `:147`, `:148`, `:154`, `:259`.
- `k1b/replay.py:85-90`, `:87`, `:88`; `llm/common.py:164-171`; `llm/fake.py:48-54`; `models.py:294-302`, `:310-312`.
- Evidence file lines: `evidence-13.md:13`, `:22`, `:23-24`, `:43-58`, `:63-73`, `:74-87`, `:99`, `:105`.

## 4. CANNOT-CHECK

1. `git apply --check` exit codes on b4cce5b copies (0, 0, 0) and on the 176a0cbe0 archive (C-01 1, A-01 0, G5 1), and the `-C1` runs: these are recorded terminal outputs; I did not re-run them (no `git apply`, static task).
2. The text "patch failed: `config.py:362`" and "Context reduced to (1/1) to apply fragment at 392" are git's own messages from an earlier session; no saved output exists to compare.
3. `/tmp/core-b4p` vs `/tmp/core-b4m` identical `src` and `tests`; `/tmp/smfull` `src` equal to the checkout: not compared (no diff run).
4. Postgres 16.15 throwaway run (`fix-patchcopies1.md`, `DEAD-MAN-CHECK.md:12-16`): the existence of the run was not verifiable; I checked only what the files say.
5. HEAD id `1be1b541e` and `76c01f662` named in the text are historic ids; the HEAD now is `3306e02aa`; the `evidence-14-provenance.md` shallow-clone statements were not re-run (no `git rev-parse` of shallow state, merge-base or reflog checks).
6. Bare `:NNN` follow-on cites whose file is only implied by earlier prose (for example "`:217`", "`:207`" with no file named in the same sentence) were checked only where the script could attach them to the file just before them (about 60 such follow-ons, all MATCH). Follow-ons separated from their file by a full sentence were not checked.
7. Line-number claims about a file "at b4cce5b plus the patches" for `tick.py`, `chain.py`, `local_dir.py` in the patched copy were not checked beyond the ones listed in section 3.
8. Prose claims that rest on a statement about what code does (for example "the model itself holds no SQL", "no producer returns a negative count", "nothing in this repository ever drains the outbox") were not tested; I opened only the cited lines.
9. The `patch-copies/README.md` section names and wording: the README is still being edited by someone else, so any quote can change; M1 shows one drift.
10. `ORDERS.md` and the `.claude/rules` files: lines 1-487 do not cite `ORDERS.md` (0 hits). Rule-file mentions (`least-privilege-hard-rule.md` item 5, the first section of `CLAUDE.md`) were read and agree.
11. `../QUEUE.md` and `../heavy-test-lane/SUMMARY.md` option A (line 26) and the 09:45 correction (line 31): quoted text was read, not tested.
12. Date and time arithmetic (UTC to IST) and the sizes in the decision table (days) were not checked; they are estimates.

## 5. What I did not do

I did not run tests, Postgres, or the network. I did not edit REVIEW.md. No personal handle or secret appears in this report. HEAD of the repository during the check: `3306e02aa`.

## 6. Totals

MATCH about 380, MISMATCH 2 (M1 at line 67, M2 at lines 73 and 323), CANNOT-CHECK 12 items.
