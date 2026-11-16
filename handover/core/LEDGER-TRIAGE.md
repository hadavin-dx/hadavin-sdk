# Ledger triage (ORDER 256 item E)

Written 2026-11-12 by the ledger-triage helper. The ledger file was only read; nothing in it was changed. Times in UTC; IST is UTC+5:30.

## What failed, what is uncertain, what I did not check (read this first)

1. **The brief described the ledger wrongly.** It said rows have 10 fields by `awk -F"|" NF==10`. Only 488 of 3045 rows do (the file also grew from 3025 to 3045 rows while I worked, appended by other sessions; every number below is from the 3045-row state, md5 d7b526fd22c5d3458ec92e8f7d19f476). By that count the rows come in four shapes: NF 7 (272 rows), NF 9 (2200 rows), NF 10 (488 rows) and NF 11 (87 rows). The column order differs between shapes: the severity is in the second cell in 707 rows and in the third cell in most others, and the package and status cells move too. 10 ids occur twice. So I wrote a parser that finds the status cell and the severity cell by their words (`/home/user/build/ledger_parse.py`). Rows it could not read as BLOCKER, MAJOR, MINOR or NIT are counted as OTHER (34 rows: notes, evidence lines, questions, "see rows" summaries).
2. **I did not verify each Blocker or Major against a later artifact one by one.** That is not possible by id: only 79 of the 1971 Blocker/Major ids are ever named again outside the ledger (reviewers write their own ids such as A1 or M2). What I did instead: (a) read the Blocker and Major counts printed at the top of every per-reviewer report file in `handover/reviews` for the build packages and decided "clean round" from those counts; (b) read by hand the Q8c-1 reconciliation table (`reviews/Q8c-1/ledger-reconciliation-r7.md`, 22 rows) and the Q8a-1 round 20 reports against the round 19 rows; (c) read the headers of P3a-2 rounds 18 and 19, PR89 rounds 26 and 27, P6a round 4. Everything else is inference from the round structure of the ledger. Each inference is labelled as such below.
3. **A clean round is judged only from reports whose first 10 lines give "N Blocker, N Major" counts.** A round where any report lacks those counts (for example `pr74/round5-textnorm.md`, most PR89 rounds 12 to 18) is NOT counted as clean. The ledger-only view would have called PR89 round 27 clean; its codebase report has 1 Major, so it is not. If I read a count wrong the rule is too strict or too loose for that package; the full list of rounds I treated as clean is in section 2.
4. **Plan-review rows (2171 rows) are findings about ticket text that was frozen on 6 Nov**, not about code. I did not try to close them (no per-finding disposition table is machine-readable). They are counted and grouped, not proposed for closing, except minors by rule R1/R2 where the rule applies.
5. **Clean rounds with no ledger rows exist** (Q8a-1 round 20 has two reports with 0 Blocker, 0 Major and 8 minors, and the ledger has no round 20 rows). Those minors (F1 to F8) are not in the ledger. They need rows; I did not add any (read-only task).
6. The apply script was not run on the real ledger. I ran it only on a scratch copy (section 4) to check the cell-count rule.
7. Not checked: whether the sensitive-class word list catches every redaction/money/security minor (it is a keyword filter: false negatives are possible, so R1 may include a security-flavoured minor whose summary uses none of the words); the `handover/evidence` folder (3455 files) was not read except by the helper searches for ledger ids; CI results; whether rows already moved on the `main` branch after the ledger was last edited.

## 1. Counts (package by severity by status)

Command (read-only, prints the three-way table to `/home/user/build/matrix.csv` and the totals below):

```
python3 /home/user/build/ledger_triage_report.py     # needs /home/user/build/ledger_parse.py, review_files.py, ledger_triage_rules.py
awk -F'|' 'NF==10' /home/user/hadavin-sdk/handover/ledger.md | wc -l    # the brief's own filter: 488, not all rows
```

Total data rows: **3045**. Duplicate ids: 10.

| severity | OPEN | FIXED-UNVERIFIED | FIXED-VERIFIED | OWNER-ONLY | IMPOSSIBLE-NOW | NOTE-OR-CLOSED | all |
|---|---|---|---|---|---|---|---|
| BLOCKER | 114 | 20 | 3 | 0 | 0 | 0 | 137 |
| MAJOR | 1605 | 187 | 14 | 19 | 7 | 2 | 1834 |
| MINOR | 860 | 20 | 17 | 8 | 0 | 0 | 905 |
| NIT | 135 | 0 | 0 | 0 | 0 | 0 | 135 |
| OTHER | 11 | 7 | 2 | 2 | 1 | 11 | 34 |
| all | 2725 | 234 | 36 | 29 | 8 | 13 | 3045 |

Per package, rows still OPEN or FIXED-UNVERIFIED by severity (B = Blocker, M = Major, m = Minor, n = Nit, o = other) and rows in the other statuses. "lineage" says whether the rows review frozen ticket text (PLAN) or built code (BUILD). Package names are cleaned from many spellings (for example a2 and PR89 are one package; PR73 is the build of P3a-2). The complete three-way table is `/home/user/build/matrix.csv` (233 lines).

| package | lineage | B | M | m | n | o | open rows | other status | all rows |
|---|---|---|---|---|---|---|---|---|---|
| A21a | BUILD | 3 | 8 | 2 | 0 | 0 | 13 | 0 | 13 |
| MAIN-MISC | BUILD | 1 | 15 | 3 | 0 | 0 | 19 | 0 | 19 |
| P0a | BUILD | 0 | 3 | 4 | 0 | 0 | 7 | 2 | 9 |
| P2a | BUILD | 1 | 7 | 0 | 0 | 0 | 8 | 0 | 8 |
| P2d | BUILD | 3 | 32 | 14 | 0 | 3 | 52 | 2 | 54 |
| P3a-2 | BUILD | 3 | 66 | 52 | 8 | 5 | 134 | 8 | 142 |
| P5a | BUILD | 1 | 21 | 12 | 3 | 3 | 40 | 6 | 46 |
| P6a | BUILD | 0 | 11 | 6 | 0 | 0 | 17 | 3 | 20 |
| PEEL-run-id | BUILD | 0 | 2 | 1 | 0 | 0 | 3 | 0 | 3 |
| PR83 | BUILD | 1 | 7 | 0 | 0 | 0 | 8 | 0 | 8 |
| PR85 | BUILD | 0 | 2 | 9 | 1 | 0 | 12 | 4 | 16 |
| PR86 | BUILD | 0 | 2 | 2 | 0 | 0 | 4 | 0 | 4 |
| PR89 | BUILD | 5 | 69 | 60 | 1 | 5 | 140 | 3 | 143 |
| PR91 | BUILD | 3 | 19 | 0 | 0 | 0 | 22 | 2 | 24 |
| PRH | BUILD | 5 | 46 | 13 | 0 | 0 | 64 | 5 | 69 |
| Q8a-1 | BUILD | 4 | 40 | 26 | 3 | 0 | 73 | 9 | 82 |
| Q8a-2 | BUILD | 0 | 6 | 4 | 0 | 0 | 10 | 0 | 10 |
| Q8a-plan | BUILD | 1 | 0 | 0 | 0 | 0 | 1 | 3 | 4 |
| Q8b | BUILD | 4 | 36 | 21 | 3 | 2 | 66 | 12 | 78 |
| Q8b-plan | BUILD | 3 | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| Q8c-1 | BUILD | 0 | 18 | 29 | 10 | 0 | 57 | 27 | 84 |
| Q8c-plan | BUILD | 4 | 0 | 0 | 0 | 0 | 4 | 0 | 4 |
| T1-T2 | BUILD | 0 | 9 | 9 | 0 | 0 | 18 | 0 | 18 |
| TIMING | BUILD | 0 | 10 | 0 | 0 | 0 | 10 | 0 | 10 |
| UNASSIGNED | BUILD | 0 | 2 | 1 | 0 | 0 | 3 | 0 | 3 |
| AK-G1 | PLAN | 7 | 46 | 0 | 0 | 0 | 53 | 0 | 53 |
| AK-G2 | PLAN | 1 | 38 | 0 | 0 | 0 | 39 | 0 | 39 |
| AK0 | PLAN | 0 | 31 | 0 | 0 | 0 | 31 | 0 | 31 |
| AK1 | PLAN | 3 | 41 | 0 | 0 | 0 | 44 | 0 | 44 |
| AK2a | PLAN | 0 | 58 | 0 | 0 | 0 | 58 | 0 | 58 |
| AK4a | PLAN | 2 | 37 | 0 | 0 | 0 | 39 | 0 | 39 |
| MAIN-MISC | PLAN | 1 | 4 | 1 | 0 | 0 | 6 | 0 | 6 |
| P0a | PLAN | 1 | 9 | 10 | 0 | 0 | 20 | 0 | 20 |
| P0c | PLAN | 1 | 5 | 8 | 2 | 0 | 16 | 0 | 16 |
| P1 | PLAN | 6 | 134 | 105 | 15 | 0 | 260 | 0 | 260 |
| P1d | PLAN | 2 | 1 | 0 | 0 | 0 | 3 | 0 | 3 |
| P1d-a | PLAN | 10 | 21 | 0 | 0 | 0 | 31 | 0 | 31 |
| P1d-b | PLAN | 1 | 2 | 1 | 0 | 0 | 4 | 0 | 4 |
| P1d-c | PLAN | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1 |
| P1d-learn | PLAN | 1 | 1 | 0 | 0 | 0 | 2 | 0 | 2 |
| P1m | PLAN | 0 | 3 | 0 | 0 | 0 | 3 | 0 | 3 |
| P2a | PLAN | 11 | 99 | 95 | 14 | 0 | 219 | 0 | 219 |
| P2d | PLAN | 0 | 50 | 57 | 10 | 0 | 117 | 0 | 117 |
| P3a | PLAN | 5 | 81 | 82 | 7 | 0 | 175 | 0 | 175 |
| P3a-2 | PLAN | 1 | 23 | 0 | 0 | 0 | 24 | 0 | 24 |
| P4a | PLAN | 6 | 93 | 75 | 25 | 0 | 199 | 0 | 199 |
| P4b1 | PLAN | 1 | 30 | 16 | 4 | 0 | 51 | 0 | 51 |
| P4b2 | PLAN | 3 | 25 | 6 | 7 | 0 | 41 | 0 | 41 |
| P4c | PLAN | 1 | 36 | 6 | 9 | 0 | 52 | 0 | 52 |
| P4d | PLAN | 5 | 89 | 103 | 7 | 0 | 204 | 0 | 204 |
| P5a | PLAN | 4 | 33 | 8 | 3 | 0 | 48 | 0 | 48 |
| P5b1 | PLAN | 0 | 23 | 19 | 1 | 0 | 43 | 0 | 43 |
| P5b2 | PLAN | 0 | 23 | 6 | 2 | 0 | 31 | 0 | 31 |
| P5b3 | PLAN | 0 | 27 | 0 | 0 | 0 | 27 | 0 | 27 |
| P5b4 | PLAN | 3 | 32 | 0 | 0 | 0 | 35 | 0 | 35 |
| P5b5 | PLAN | 1 | 21 | 0 | 0 | 0 | 22 | 0 | 22 |
| P5c | PLAN | 2 | 42 | 0 | 0 | 0 | 44 | 0 | 44 |
| P6a | PLAN | 1 | 23 | 0 | 0 | 0 | 24 | 0 | 24 |
| P6b1 | PLAN | 0 | 17 | 14 | 0 | 0 | 31 | 0 | 31 |
| P6b2 | PLAN | 1 | 29 | 0 | 0 | 0 | 30 | 0 | 30 |
| P8a | PLAN | 0 | 25 | 0 | 0 | 0 | 25 | 0 | 25 |
| P8b | PLAN | 6 | 30 | 0 | 0 | 0 | 36 | 0 | 36 |
| lookalike | PLAN | 5 | 78 | 0 | 0 | 0 | 83 | 0 | 83 |

## 2. Minors and nits that can close as ACCEPTED-NIT

Minors and nits that are OPEN or FIXED-UNVERIFIED: **1015** (880 minors, 135 nits). Never a Blocker or Major.

Rules (applied in this order; a row falls into the first that matches):

- **R1 (proposed for apply, default in the script): 84 rows.** The row is a Minor or Nit; OPEN or FIXED-UNVERIFIED; its package has a later or same review round whose reports show 0 Blocker and 0 Major; and the row is not in the sensitive class (words: redact, leak, secret, password, credential, token, money, spend, budget, approval, permission, least privilege, grant, tenant, isolation, injection, tamper, mask, hmac, kill switch, executor, exfil, forge, replay, idempotent, stage, mode safety) and not waiting for the lead or owner. Reason written into the status: "ACCEPTED-NIT (was OPEN; rule R1: minor, not a security/money/redaction/mode-safety class, round N reviewed clean: <report>)" (the script lists 83 of these under R1 and the 84th, `Q8c-1-r3-cb-m4`, under MANUAL because its closing line was read by hand). This is ORDER 256 correction A applied to the ledger: a minor after a clean round is fixed in one push without a new review, so it must not stay as an open blocker-style row.
- **SENS: 136 rows** are minors in the sensitive class. They stay OPEN. Security, money and redaction minors are not closed by a keyword rule; a person or a reviewer reads them.
- **HOLD: 14 rows** wait for a lead or owner decision (text says PENDING LEAD, NEEDS LEAD, OWNER-ONLY, lead decision). They stay.
- **R2 (optional, off by default, needs the lead's yes): 633 rows.** Minors or nits, not sensitive, not waiting, from a round at least 2 rounds older than the last round of the same package and lineage. Basis: the review-loop-speed rule (after round 2 minors are batch-fixed without a new review). Weak point, said plainly: nothing proves these minors were fixed or are no longer raised; "accepted" here means "will not block and will not get its own review". Apply script flag `--r2`.
- **REST: 148 rows** (round-less rows, or in the latest rounds of a package, or in packages with no clean round). They stay OPEN until their package gets a clean round or the lead decides.

Rounds I treated as clean (all per-reviewer reports parsed with 0 Blocker and 0 Major, and no OPEN Blocker/Major ledger row of that round): P3a-2 rounds 18, 19; P6a rounds 4; PR87 rounds 2; PR89 rounds 4, 5, 8, 9; Q8a-1 rounds 10, 20; Q8a-2 rounds 4; Q8c-1 rounds 7, 8. Plan-lineage clean rounds by ledger rows: none.

R1 coverage by package (ledger line numbers of the rows; full list with ids and the clean-round report in `/home/user/build/r1_rows.csv`):

| package | R1 rows | OPEN | FIXED-UNVERIFIED | first id | last id | ledger lines | clean round used and report |
|---|---|---|---|---|---|---|---|
| P3a-2 | 41 | 38 | 3 | BL-core-a5-w2-02 | P3a2b8-r19-9 | 2233-3040 | r19: reviews/p3a-2/p3a2b8-design-r19.md; reviews/p3a-2/p3a2b8-codebase-r19.md |
| P6a | 5 | 3 | 2 | BL-core-a14-w2-08 | BL-core-a14-w2-r4-01 (update) | 2231-2325 | r4: reviews/p6a/round-w2-r4-codebase.md |
| PR89 | 6 | 4 | 2 | BL-core-a2-w2-r2-03 | BL-core-a2-w2-r9-02 | 2287-2366 | r9: reviews/p89/round-w2-r9-codebase.md; reviews/p89/round-w2-r9-design.md |
| Q8a-1 | 19 | 19 | 0 | Q8a1-r10-G1 | Q8a1b18-r19-9 | 2740-3016 | r20: reviews/q8a-1/q8a1b19-design-r20.md; reviews/q8a-1/q8a1b19-codebase-r20.md |
| Q8a-2 | 4 | 4 | 0 | BL-core-q8a2-r2-c02 | Q8a-2-r4-m3m4 | 2642-2710 | r4: reviews/q8a-2/result-r4-codebase-full.md |
| Q8c-1 | 9 | 7 | 2 | Q8c-1-r3-cb-m4 | Q8c1b8-r8-E3 | 2699-2786 | r8: reviews/q8c-1/q8c1b8-codebase-r8.md; reviews/q8c-1/q8c1b8-design-r8.md |

Summary of the 1015 open-like minors and nits: R1 84, SENS 136, HOLD 14, R2 633, REST 148.

Minors by package that no rule closes (SENS + HOLD + REST): P4d 30, P2d 26, P2a 24, PR89 24, P3a 21, P5b1 20, P3a-2 19, Q8c-1 19, P0a 14, Q8b 13, P5a 11, P0c 10.

## 3. Blockers and Majors: what truly remains

There are **1971** Blocker/Major rows (137 Blocker, 1834 Major). I split the OPEN and FIXED-UNVERIFIED ones into groups. "Closed" below means: not an open ledger row; it does NOT mean I proved the fix in the code.

| group | rows | Blocker | Major | of them FIXED-UNVERIFIED |
|---|---|---|---|---|
| C0 already closed, owner-only or impossible-now in the ledger | 45 | 3 | 42 | 0 |
| C1 BUILD: a later review round was clean (0 Blocker, 0 Major) | 127 | 8 | 119 | 14 |
| C2 BUILD: no later clean round (REMAINING list) | 346 | 34 | 312 | 21 |
| C3a PLAN text: older than the last round of its ticket | 1153 | 79 | 1074 | 135 |
| C3b PLAN text: last round of its ticket or round-less | 300 | 13 | 287 | 37 |

- **C0 (45 rows)**: the ledger already says FIXED-VERIFIED, OWNER-ONLY or IMPOSSIBLE-NOW (the Q8c-1 reconciliation was already applied: its 22 table verdicts match the ledger except one row, `Q8c-1-r3-cb-m4`, which the table moves from FIXED-UNVERIFIED to FIXED-VERIFIED; I included that one row as a manual proposal).
- **C1 (127 rows) can be closed with an artifact.** These are build-lineage Blocker/Major rows from a round older than a round whose per-reviewer reports (fresh reviewers, reading the later head) show 0 Blocker and 0 Major. The closing artifact is that round's report; a fresh reviewer reading the later head did not report them, so they were fixed or reclassified. Proposed status FIXED-VERIFIED with the report path. Off by default (`--bm-clean`) because it is inference at package level: 72 of the rows are covered by two clean rounds in a row (strong), the rest by one. Rows named in the clean round itself as incomplete (Q8a-1 r19 items 6 and 11) are excluded. By package: P3a-2 56, Q8a-1 40, PR89 16, P6a 9, Q8a-2 6.
- **C3a (1153 rows) and C3b (300 rows)** are findings on frozen ticket text (PLAN). C3a: a later round of the same ticket exists and each round has a resolve report (which I did not parse), so these findings were probably applied or declined in a later ticket revision that was reviewed again; I cannot tell which were declined. C3b: findings of the last round of the ticket (applied into the final frozen revision, which the freeze list says is unreviewed text), or round-less. None of these is proposed for closing. They close when the built pull request's review covers them. Per-ticket counts and every row: `/home/user/build/plan_bm_by_ticket.csv`.
- **C2 (346 rows) are the Blockers and Majors that truly remain** on built code (no later clean round, not closed in the ledger). Every one is listed in section 3.2, grouped by bug class. Some of them may already be fixed by a builder batch that has no ledger row yet; the lead should expect the real number to be lower, but I cannot show it.

### 3.1 Remaining (C2) by package

| package | Blocker | Major | of them FIXED-UNVERIFIED | last round in the ledger | latest clean round (reports) |
|---|---|---|---|---|---|
| PR89 | 4 | 54 | 8 | 27 | 9 |
| PRH | 5 | 46 | 0 | 11 | none |
| Q8b | 4 | 36 | 3 | 14 | none |
| P2d | 3 | 32 | 1 | 7 | none |
| PR91 | 3 | 19 | 1 | 3 | none |
| P5a | 1 | 21 | 0 | 6 | none |
| Q8c-1 | 0 | 18 | 0 | 15 | 8 |
| MAIN-MISC | 1 | 15 | 0 | 0 | none |
| P3a-2 | 0 | 13 | 0 | 19 | 19 |
| A21a | 3 | 8 | 1 | 3 | none |
| TIMING | 0 | 10 | 0 | 2 | none |
| T1-T2 | 0 | 9 | 3 | 3 | none |
| PR83 | 1 | 7 | 0 | 3 | none |
| P2a | 1 | 7 | 0 | 2 | none |
| Q8c-plan | 4 | 0 | 0 | 2 | none |
| Q8a-1 | 0 | 4 | 0 | 19 | 20 |
| P0a | 0 | 3 | 1 | 2 | none |
| Q8b-plan | 3 | 0 | 0 | 2 | none |
| PEEL-run-id | 0 | 2 | 1 | 0 | none |
| P6a | 0 | 2 | 0 | 4 | 4 |
| PR86 | 0 | 2 | 0 | 3 | none |
| UNASSIGNED | 0 | 2 | 1 | 3 | none |
| PR85 | 0 | 2 | 0 | 6 | none |
| Q8a-plan | 1 | 0 | 1 | 2 | none |

### 3.2 Remaining (C2) grouped by bug class

Class is assigned by keywords on the summary (first match wins; "other" means no keyword matched). It is a reading aid, not a verdict. Full text of each summary: `/home/user/build/remaining_bm_build.csv`.

#### redaction / text-normalisation hole (secret shown after look-alike, marks, escapes, control characters) (73 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-q8red-F1 | MAIN-MISC | Blocker | OPEN | see reviews/Q8/redaction-sweep.md F1 (reproduced with neutralise=None only) |
| BL-core-q8red-F2 | MAIN-MISC | Major | OPEN | see reviews/Q8/redaction-sweep.md F2 |
| BL-core-q8red-F3 | MAIN-MISC | Major | OPEN | see reviews/Q8/redaction-sweep.md F3 |
| BL-core-q8red-F4 | MAIN-MISC | Major | OPEN | see reviews/Q8/redaction-sweep.md F4 |
| BL-core-q8red-F5 | MAIN-MISC | Major | OPEN | see reviews/Q8/redaction-sweep.md F5 |
| BL-core-q8red-F6 | MAIN-MISC | Major | OPEN | see reviews/Q8/redaction-sweep.md F6 |
| BL-core-q8red-F7 | MAIN-MISC | Major | OPEN | see reviews/Q8/redaction-sweep.md F7 |
| BL-core-q8red-F5c | MAIN-MISC | Major | OPEN | k1b sensitive() misses PGPASSWORD/pwd/DBPassword and non-string env values: values returned unmasked (REPRODUCED by l... |
| BL-core-a11a-w2-01 | P2d | Major | OPEN | evidence ran on a head that does not contain current core/P1a (27ae996); P2d-1 merges 2572847; ruff format --check fa... |
| BL-core-a11a-w3-04 | P2d | Major | OPEN | redactor scans fold only, not fold_views/squeeze_views; Mc/Lm/Sk and Greek+U+0345 split a key (redaction, uncapped) |
| BL-core-a11a-w4-s01 | P2d | Major | OPEN | masked value keeps leading/trailing Mc/Lm/Sk in clear: "café password=Hunter2abc^" -> "<SECRET_1>^" (redact.py:1301-1... |
| BL-core-a11a-w4-s01-fix | P2d | Major | FIXED-UNVERIFIED | edge-marks Major BL-core-a11a-w4-s01 fixed at `_mask_in_place(marks=...)`; test_marks_16 fails on 62acddd; mutants W1... |
| BL-core-a11a-w5-s01 | P2d | Major | OPEN | strip_ansi redact.py:835-852 cuts a real ESC[..m / ESC[F / U+009B digit-letter sequence out of a key; halves stay in ... |
| BL-core-a11a-w5-s02 | P2d | Major | OPEN | strip_ansi swallows the letter after ESC/U+009B when not between two word chars (`id: \x9bpassword=Hunter2abc` -> `as... |
| BL-core-a11a-w5-s03 | P2d | Major | OPEN | `_HIDDEN_ASCII` redact.py:947-949 joins a tab only between ASCII letters/digits; `x ghp_\tIOSFODNN7EXAMPLEIOSFODNN7EX... |
| BL-core-a11a-w6-c01 | P2d | Major | OPEN | tab-run views and escape views never combine: `user\tAKIAIOSF\tODNN7\x1b[1mEXAMPLE e` -> `user\t<APIKEY_1>EXAMPLE e` ... |
| BL-core-a11a-w6-a01 | P2d | Major | OPEN | _SEP_KEEP=3: glue tab as 4th+ run leaves 3+ key characters visible (`a\tb\tc\td\tAKIAIOSFODNN\t7EXAMPLE e`, ghp_ vari... |
| BL-core-a11a-w6-a02 | P2d | Major | OPEN | escape views and tab-run views never combine: `user\tAKIA\x1b[0mIOSF\tODNN7EXAMPLE e` whole key in clear (same class ... |
| BL-core-a11a-w6-a03 | P2d | Major | OPEN | no clock check in _folded_line post-loop/_withhold/_register_written/view building; ASCII tab table can finish above ... |
| BL-core-a5-w2-r3-03 (update) | P3a-2 | Major | OPEN | Independent runner at cb0930f stopped (head will change); partial folder deleted; the sandbox refused the PG 17 wheel... |
| BL-core-a15-r1-01 | P5a | Major | OPEN | PR titled P5a carries textnorm/confusables/1.3 MB data/CHANGELOG P1a-P1b; moved-vs-duplicate unclear; split or state |
| BL-core-a15-r2-01 | P5a | Blocker | OPEN | CHANGELOG says "Python 3.13 or later"; code refuses any interpreter not on Unicode 15.1.0 |
| BL-core-a15-r2-05 | P5a | Major | OPEN | scan time budget in textnorm.py has no mutant and the mutant file was not re-run |
| BL-core-a15-w3-01 | P5a | Major | OPEN | M1 scan_keyset has no clock; fix1 note G7 says REDACT_BUDGET_S refusal; redaction path |
| BL-core-a15-w4-c01 | P5a | Major | OPEN | fold() keeps Mc though docstring :101-102 says any combining mark is dropped: fold("admin"+U+093E) != fold("admin"); ... |
| BL-core-a15-w5-c01 | P5a | Major | OPEN | textnorm.py:101-102 mark property false for whitespace controls: fold("admin\n")=="admin " != fold("admin"); add exem... |
| BL-core-a19-r1-01 | PR83 | Major | OPEN | check_id name blacklist leaves 1-2 char and short all-digit ids unrefused (leak class); derive thresholds from redact... |
| BL-core-a19-r2-01 | PR83 | Blocker | OPEN | check_id validates casefolded id but returns raw; sharp-s and long Cf ids accepted yet not masked by redactor (read-o... |
| BL-core-a19-r2-03 | PR83 | Major | OPEN | pure-punctuation ids (---, ___) accepted, may leak on sweep |
| BL-core-a19-r3-01 | PR83 | Major | OPEN | redactor `_replace_standalone` is case-sensitive: later copy of a registered id in another case stays in clear (pre-e... |
| BL-core-a2-ci-01 | PR89 | Major | OPEN | CI security job (gitleaks 8.30.1) on PR89 head 386875c: generic-api-key tests/test_mutation_runner_keywords.py:675 |
| BL-core-a2-ci-01 (update) | PR89 | Major | OPEN | Head file clean; the literal remains in history on commit 386875c (gitleaks on whole branch: 1 leak, on 386875c..HEAD... |
| BL-core-a2-w2-r10-01 | PR89 | Major | OPEN | Build pattern for secrets under FRAGMENT_MIN from the secret as written with mandatory [\\'"]+ runs; no-leak test dep... |
| BL-core-a2-w2-r10-03 | PR89 | Major | OPEN | Replace with a real test (whole value under 6 kept letters printed 3 times) or, with r10-01 fixed, a no-leak test |
| BL-core-a2-w2-r11-03 | PR89 | Major | OPEN | mask any 2-3+ character head/tail beside a literal "..." (max 1,000 hits), or state the 5-character exposure in CHANG... |
| BL-core-a2-w2-r11-01..04 | PR89 | Major | FIXED-UNVERIFIED | r11-01 run pattern short secrets only; r11-03 EDGE_MIN=2 pieces beside "..." masked; r11-04 password pieces, tests, C... |
| BL-core-a2-w2-r13-03 | PR89 | Major | OPEN | re-encoded/double-decoded password forms unmasked (M1) |
| BL-core-a2-w2-r13-07 | PR89 | Major | OPEN | no secret test for COLLECTION/FIXTURE ERROR message masking (F1) |
| BL-core-a2-w2-r13-12 | PR89 | Major | OPEN | 47 deleted tests: 'never weakened' unverifiable from diff; independent check against b855a8f needed (deletion table w... |
| BL-core-a2-w2-r14-04 | PR89 | Blocker | OPEN | test pins a masking gap as expected behaviour: '12/45' not masked (B3) |
| BL-core-a2-w2-r14-11 | PR89 | Major | OPEN | URL path / unexplained userinfo carries password into lock name (M2); refusal and masking reach beyond the password (M4) |
| BL-core-a24-r3-04 | PR91 | Major | OPEN | .gitattributes -diff/binary may blind gitleaks history scan (unprobed) |
| PRHb6-r6-F2 | PRH | Major | OPEN | Issue 3: piece check withholds whole result after every copy was masked (word-like secret; secret containing SECRET) |
| PRHb6-r6-C1 | PRH | Major | OPEN | Issue 5: direct redact() gated on ESC only; U+009B tail readable |
| PRHb6-r6-C2 | PRH | Major | OPEN | Issue 6: direct redact() picks consuming reading by placeholder count; tie keeps key tail |
| PRHb6-r6-E3 | PRH | Major | OPEN | Issue 8: public redact() leaves ZW/bidi-cut keys readable (existing gap) |
| PRHb7-r7-i9 | PRH | Major | OPEN | r7 F1/D1: spaced-out secret treated as owner-only; known values (map, sweep, tool scrub) must be masked now; "three r... |
| PRHb7-r7-direct | PRH | Major | OPEN | r7 D3: direct redact() shows 17+ key characters when an escape or opener eats a capital letter and the map is fresh |
| PRHb8-r8-1 | PRH | Blocker | OPEN | r8 D1/B1/M2: mutant gate red (109 of 114): 54, 84, 93, 111 survive, 59 wrong reason; live guards no test needs; 54 ca... |
| PRHb8-r8-2 | PRH | Major | OPEN | r8 D2: (fj, fs) fold neither proven dead nor justified: keep, construct the input, pin with a mutant |
| PRHb8-r8-5 | PRH | Major | OPEN | r8 D5/M1: spaced-run bypasses (other whitespace, glued key, keyed value, punctuation, unknown shape); evidence leak g... |
| PRHb9-r9-4 | PRH | Major | OPEN | r9 security: ordinary text withheld 1.59 percent vs main 0.87 percent and SECURITY sentence misdescribes it; final gu... |
| PRHb10-r10-4 | PRH | Major | OPEN | r10 RedactorCrash swallowed as no values found in the remnant check and sibling catchers; docstring and CHANGELOG cla... |
| PRHb10-r10-8 | PRH | Major | OPEN | r10 evidence: literal backslash-e spelling inside a secret is readable on head (hand-out value and token-shaped, mid ... |
| Q8b-r1-F2 | Q8b | Major | OPEN | LIMITS text says always masked but UTC-time and setting-key exceptions exist (ticket text; fix on ticket side) |
| Q8b-r2-1..7 | Q8b | Blocker | FIXED-UNVERIFIED | long glued key (any length), one key list, card keeps its words, tail of a value with spaces masked on every path, li... |
| Q8bb7-i1-5 | Q8b | Major | FIXED-UNVERIFIED | r7 Issues 1-5 (digit-glued flag keys, plural flags, Cookie keys, Authorization scheme words, over-masking of bypass/c... |
| Q8bb7-r8-i1 | Q8b | Major | OPEN | r8 Issue 1: plural `tokens` flag readable after glued/camelCase word (`--apiTokens`, `--accesstokens`); fix with one ... |
| Q8bb8-r9-c1 | Q8b | Major | OPEN | r9 C1: wrapped `Authorization: Basic/Token/ApiKey<LF>` header leaks its credential (regression vs main; redact.py:731... |
| Q8bb9-r10-1 | Q8b | Blocker | OPEN | r10 R10-1/F1: wrapped Authorization token of 8-15 chars, early dot/tilde/colon, lowercase-only, and Token/ApiKey/Dige... |
| Q8bb9-r10-2 | Q8b | Major | OPEN | r10 F2/F3: Digest header folded over more than one line leaves response hash readable; CHANGELOG item 1 says Digest u... |
| Q8bb10-r11-8 | Q8b | Major | OPEN | r11 evidence (lead-assigned severity): continuation lines after Basic/Token/ApiKey/Bearer folded headers readable (72... |
| Q8bb11-r12-1 | Q8b | Major | OPEN | r12 regressions against main: 16 plus 340 probe cells (bare compass overpass encompass bypass and json ordinary-word ... |
| Q8bb11-r12-4 | Q8b | Major | OPEN | r12 folded-header class not closed: shape A 273 of 979 and shape C 807 of 979 readable; scheme words beyond five; ext... |
| Q8bb12-r13-1 | Q8b | Blocker | OPEN | r13 prefilter skips a key word that overlaps the previous gate hit (accessession, xpassession, passecret): main masks... |
| Q8bb12-r13-2 | Q8b | Blocker | OPEN | r13 wide scheme-word class leaves a capital-first hyphenated token readable that main masked (Ab12-Cd34-Ef56, Correct... |
| Q8bb12-r13-3 | Q8b | Major | OPEN | r13 new any-scheme fold rule quadratic on a glued run of 15000 small objects (unbounded first word) |
| Q8bb12-r13-5 | Q8b | Major | OPEN | r13 prefixed keys x-bypass new_bypass x_compass readable on head, main masked; statement wider than code |
| Q8bb13-r14-1 | Q8b | Major | OPEN | r14 design D1: x--bypass x--compass x--overpass x--possession readable on head and masked on main (confirmed by lead ... |
| Q8bb13-r14-6 | Q8b | Major | OPEN | r14 evidence gate: no independent full evidence on 120f3f78 (heavy queue full); builder stage and runner mutants ran ... |
| BL-core-q8b-plan-r2-B1 | Q8b-plan | Blocker | OPEN | reviews/Q8b/plan-r2-full.md B1 (rev 2's setting-word rule unmasks credentials main masks) |
| BL-core-a21a-w2-r2-02 | T1-T2 | Major | FIXED-UNVERIFIED | concurrent-caller race has no test in repo; seed only in scratch folder |
| BL-core-a21a-w2-r3-01 | T1-T2 | Major | OPEN | CI-guard change: no green CI nor independent run yet; ci.yml pytest step count disagrees (2 vs 3); PR body points at ... |

#### test gap, mutant gap or vacuous test (a check that cannot fail) (63 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-a21a-w2-06 | A21a | Blocker | OPEN | `# fmt: skip` suppression in tests/test_t1_meter_parallel.py:28 |
| BL-core-a21a-w2-08 | A21a | Major | OPEN | duplicated test bodies between T2 replay file and contract file; mutant only_test ids depend on them |
| BL-core-a21a-w2-12 | A21a | Blocker | OPEN | Postgres kill proof not reproducible: postgres_mutants.py not in the diff; P3 killed by a CHECK constraint, not a tim... |
| BL-core-a21a-w2-r3-01 (evidence note) | A21a | Major | FIXED-UNVERIFIED | Independent run at 1a7d202 (Postgres 16 only, own cluster on port 5432): ruff/format/bandit/scan_repo exit 0; full su... |
| BL-core-a22-w2-02 | P0a | Major | OPEN | test_no_pglast_in_runtime.py not run on real main: fails if demos/ or tools/ hold no .py; may scan a nested .venv |
| BL-core-a22-w2-02b | P0a | Major | FIXED-UNVERIFIED | evidence runner (evidence/P0a/151d3e1-cloud/TABLE.md): test passes 21/21 on py3.13 (py3.12 not run); origin/main hold... |
| BL-core-a10a-w2-04 | P2a | Major | OPEN | test_cli_kill_switch_reaches_every_process lost its reset leg (weakened test) |
| BL-core-a11a-w3-01 | P2d | Major | OPEN | test_digits_1 card half cannot fail (space-grouped card, 8-digit run) |
| BL-core-a11a-w6-t01 | P2d | Major | OPEN | two ANSI sequences in one key (`user\x1b[0mAKIAIOS\x1b[0mFODNN7EXAMPLE e`); tab-keep view without ANSI mode (`user\tA... |
| BL-core-a11a-w6-t02 | P2d | Major | OPEN | 8 mutants with `old` text matching 0 times (W4, W5, W11, W16, W19, mutant 6, N9, N14) |
| P3a2-3c-C2 | P3a-2 | Major | OPEN | step-4 REVOKE escape ascii-based for quoted/non-ASCII function names, untested |
| BL-core-a15-r1-03 | P5a | Major | OPEN | pilot/prod refused on py3.12 not in Upgrade steps; guard stubbed in tests on 3.12 |
| BL-core-a15-r1-06 | P5a | Major | OPEN | old-writers test is a status ledger, evidence.md missing, dead no_path branch |
| BL-core-a15-r2-03 | P5a | Major | OPEN | ticket-required tests missing; test_row validation path partial; literal counts; old-writer reasons |
| BL-core-a15-r2-04 | P5a | Major | OPEN | mutation plan lacks many Appendix B mutants |
| BL-core-a15-r2-06 | P5a | Major | OPEN | test file name differs from ticket gate command |
| BL-core-a15-r2-02 | P5a | Major | OPEN | `_own_code` type check wrongly called equivalent; no test with a hostile __str__ |
| BL-core-a15-w3-03 | P5a | Major | OPEN | T1 gate test-file name drift (rc 4); T2 test_reverse_check_fails_90_percent absent; T3 teeth test weaker than BN-3; T... |
| BL-core-a14-w2-05 | P6a | Major | OPEN | strict-bool sweep over 7 src files not in the ticket; no old-code run of tests/test_strict_flags.py |
| BL-core-a17-w3-02 | PR85 | Major | OPEN | ~140 OPERATOR/FOREIGN CSV labels unverified; needs reviewer with full tree + test/mutant/cmp run |
| BL-core-a2-w2-r11-01 | PR89 | Major | OPEN | return None from _run_pattern when len(kept) >= FRAGMENT_MIN plus test, or fix docs |
| BL-core-a2-w2-r13-01 | PR89 | Major | FIXED-UNVERIFIED | PR89 round 12 builder report (head 0cd10b9, tree adb8973c) |
| BL-core-a2-w2-r13-08 | PR89 | Major | OPEN | canary-skip message never tested with a secret (F2) |
| BL-core-a2-w2-r13-09 | PR89 | Major | OPEN | baseline-skip test can pass for the wrong reason (F3) |
| BL-core-a2-w2-r13-10 | PR89 | Major | OPEN | fake credentials not built from parts, ~20 places (F4) |
| BL-core-a2-w2-r13-16 | PR89 | Major | OPEN | conftest guard mutants missing (M4) |
| BL-core-a2-w2-r14-01 | PR89 | Major | FIXED-UNVERIFIED | PR89 round 13 builder report (head e957592, tree 52c696f8) |
| BL-core-a2-w2-r14-08 | PR89 | Major | OPEN | whole-literal fake secrets at 560-561 and 625-630 |
| BL-core-a24-r1-01 | PR91 | Blocker | OPEN | tests/test_ci_toolpath_step.py has 6 unlisted noqa S603/S607 lines; own scan job and real-repo test should fail |
| BL-core-a24-r1-03 | PR91 | Major | OPEN | suppression count is per line not per marker/content; widen or move passes; pin hash |
| BL-core-a24-r3-01 | PR91 | Major | OPEN | known-binary extension with NUL skips all secret patterns; test pins it |
| BL-core-a24-r3-03 | PR91 | Major | OPEN | guard tests can be disabled via conftest/pytest.ini/pyproject pytest keys, not code-owned or pinned |
| BL-core-a24-r3-08 | PR91 | Major | OPEN | codeql-config.yml/zizmor.yaml/checkov/hadolint not scanner config; CODEOWNERS lacks test_no_reference_material.py |
| PRHb7-r7-compare | PRH | Major | OPEN | r7 F2/D2: `compare_readings` shared in name; conflict branch runmap.py:629-633 unreachable, no mutant |
| PRHb9-r9-2 | PRH | Major | OPEN | r9 docs and tests that cannot fail: docs test self-referential, hyphen docs vs code, 898 of 3000 and 47 tests unsuppo... |
| PRHb9-r9-5 | PRH | Major | OPEN | r9 wrapper characters glued to a spaced run (backtick asterisk and others) defeat the run rule; encoded-gap unknown v... |
| PRHb10-r10-1 | PRH | Major | OPEN | r10 wrapper rule is a 9-character allowlist so curly quotes and other glue characters still defeat the spaced-key rul... |
| PRHb10-r10-2 | PRH | Major | OPEN | r10 n1 dropped-view secret-kind restriction has no killer or mutant and compare-copies half of r9 group 5 not done |
| PRHb10-r10-3 | PRH | Major | OPEN | r10 SECURITY.md still states the withdrawn 898 of 3000 figure; docs test cannot see it; CRASH definition and cited ge... |
| PRHb11-r11-4 | PRH | Major | OPEN | r11 F4: docs figure tests cannot fail, ghost mutant numbers, no error_reason mutant |
| PRHb11-r11-5 | PRH | Major | OPEN | r11 F1: 457 skipped tests not broken down; builder and runner pytest counts differ unexplained |
| PRHb11-r11-13 | PRH | Major | OPEN | r11 evidence gate: b10 wrapper test cause unexamined, docs failures runner artefact, timing flake, probes miss catche... |
| Q8a1b18-r19-11 | Q8a-1 | Major | OPEN | r19 evidence: final file not fail-before measured, 29 tests not 30, runner missed non-dict shapes, pytest counts differ |
| Q8bb8-r9-c2 | Q8b | Major | OPEN | r9 D9-2/C2: 47 of 74 controls have no planted fault; lines file and mutant table disagree; tautological check; weak e... |
| Q8bb9-r10-3 | Q8b | Major | OPEN | r10 R10-2/F4: r9 Issue 3 still open: 28 controls with no planted fault or reason, 7 untrue NO_FAULT reasons, UNPLANTE... |
| Q8bb11-r12-2 | Q8b | Major | OPEN | r12 mutant gate not green: 212 of 229 good; M159 M163 M190 survive; M192 M198 M199 M200 M215 M216 wrong reason; M193 ... |
| Q8c1b10-r10-c1 | Q8c-1 | Major | OPEN | r10 C10-1: date tests and runner fail on partial renewal / empty lists (the first honest renewal on 2026-12-12 breaks... |
| Q8c1b10-r10-d1 | Q8c-1 | Major | OPEN | r10 D10-1: tools/notes_lines_check.py can pass with a missing id and does not see a weakened test |
| Q8c1b11-r11-1 | Q8c-1 | Major | OPEN | r11 D11-1/M2: end-state test fakes a state real rules cannot reach; real --check/--write exit 1 with both lists empti... |
| Q8c1b11-r11-3 | Q8c-1 | Major | OPEN | r11 D11-4/D11-8/m7: notes check blind to tests.* imports, mutants file, conftest, fixtures, autouse; substring reason... |
| Q8c1b12-r12-1 | Q8c-1 | Major | OPEN | r12 D12-1/M1/m5: notes check misses a PR that changes only a helper or a file imported by an unchanged test; import t... |
| Q8c1b12-r12-2 | Q8c-1 | Major | OPEN | r12 D12-2: module-level pytestmark or conftest state can switch off every test with no row required |
| Q8c1b12-r12-3 | Q8c-1 | Major | OPEN | r12 D12-3/m1: hard-coded days at test_policy_guard.py 1672-1678, 5398-5406, 220, 2888 fail on the first renewal (2026... |
| Q8c1b12-r12-4 | Q8c-1 | Major | OPEN | r12 M2/D12-4: overdue message for kinds names the wrong list and omits KINDS_DECIDED, the pin, _PR2 and the policy_mu... |
| Q8c1b13-r13-1 | Q8c-1 | Major | OPEN | r13 notes-check blind spots: assignment values not followed, conftest glue and pytest config not units, test-class he... |
| Q8c1b14-r14-3 | Q8c-1 | Major | OPEN | r14 notes check exits 0 with a used unit changed: walrus constant, unittest setUp, usefixtures and getfixturevalue, p... |
| Q8c1b15-r15-1 | Q8c-1 | Major | OPEN | r15 N1: unreadable run-time import name lists no test when the file imports any tests package; keyword name= not read... |
| BL-core-a21a-w2-03 | T1-T2 | Major | OPEN | four deliberately failing tests in tests/test_t1_meter_parallel.py would turn main red; no xfail allowed |
| BL-core-a21a-w2-04 | T1-T2 | Major | FIXED-UNVERIFIED | postgres has no cross-agent isolation test, no month-total test, no recorded mutant artifact |
| BL-core-a21a-w2-r2-01 | T1-T2 | Major | OPEN | CI guard changes a shared test helper repo-wide; no proof CI passes with it; rule duplicated from tests/demo_askdata/... |
| BL-core-a21a-w2-r2-03 | T1-T2 | Major | OPEN | NaN/negative/Infinity charges: no pinning test or in-repo note in the branch |
| timing-r1-D-M3 | TIMING | Major | OPEN | guard tests cannot pass on win32 |
| timing-r1-D-4 | TIMING | Major | OPEN | sentinel runmap test has no control |

#### other / unclassified (62 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-a21a-w2-15 | A21a | Major | OPEN | no harness negative control with a stub meter |
| BL-core-q8deps-F1 | MAIN-MISC | Major | OPEN | see reviews/Q8/deps-audit.md F1 |
| BL-core-q8deps-F2 | MAIN-MISC | Major | OPEN | see reviews/Q8/deps-audit.md F2 |
| BL-core-q8deps-F3 | MAIN-MISC | Major | OPEN | see reviews/Q8/deps-audit.md F3 |
| BL-core-q8deps-F4 | MAIN-MISC | Major | OPEN | see reviews/Q8/deps-audit.md F4 |
| BL-core-q8deps-F5 | MAIN-MISC | Major | OPEN | see reviews/Q8/deps-audit.md F5 |
| BL-core-q8deps-F6 | MAIN-MISC | Major | OPEN | see reviews/Q8/deps-audit.md F6 |
| BL-core-a11a-w7-M3 | P2d | Major | OPEN | reviews/PR77/round7-design.md M3 (M3-M5 reproduced by lead) |
| BL-core-a11a-w7-M4 | P2d | Major | OPEN | reviews/PR77/round7-design.md M4 (M3-M5 reproduced by lead) |
| BL-core-a11a-w7-M5 | P2d | Major | OPEN | reviews/PR77/round7-design.md M5 (M3-M5 reproduced by lead) |
| BL-core-a11a-w7-M6 | P2d | Major | OPEN | reviews/PR77/round7-design.md M6 (M3-M5 reproduced by lead) |
| BL-core-a11a-w7-M7 | P2d | Major | OPEN | reviews/PR77/round7-design.md M7 (M3-M5 reproduced by lead) |
| BL-core-a11a-w7-M8 | P2d | Major | OPEN | reviews/PR77/round7-design.md M8 (M3-M5 reproduced by lead) |
| BL-core-a11a-w7-cM1 | P2d | Major | OPEN | reviews/PR77/round7-codebase.md M1 (M1, M2, M4 reproduced by lead) |
| BL-core-a11a-w7-cM2 | P2d | Major | OPEN | reviews/PR77/round7-codebase.md M2 (M1, M2, M4 reproduced by lead) |
| BL-core-a11a-w7-cM3 | P2d | Major | OPEN | reviews/PR77/round7-codebase.md M3 (M1, M2, M4 reproduced by lead) |
| BL-core-a11a-w7-cM4 | P2d | Major | OPEN | reviews/PR77/round7-codebase.md M4 (M1, M2, M4 reproduced by lead) |
| BL-core-a11a-w7-cM5 | P2d | Major | OPEN | reviews/PR77/round7-codebase.md M5 (M1, M2, M4 reproduced by lead) |
| BL-core-a11a-w7-cM6 | P2d | Major | OPEN | reviews/PR77/round7-codebase.md M6 (M1, M2, M4 reproduced by lead) |
| BL-core-a11a-w7-cM7 | P2d | Major | OPEN | reviews/PR77/round7-codebase.md M7 (M1, M2, M4 reproduced by lead) |
| P3a2-3c-M5 | P3a-2 | Major | OPEN | MT1/MT2 MAINTAIN retired, no killer |
| BL-core-a15-r2-05 | P5a | Major | OPEN | PR stacks P1a/P1b (~24k lines), behaviour change vs ticket; rebase or declare order |
| BL-core-a15-r1-resolve | P5a | Major | OPEN | OPEN (fix builder a621dcb9b3aacb063) |
| BL-core-a14-w2-12 | P6a | Major | OPEN | strict-bool sweep should be its own pull request (reviewer view); breaking change, no order covers it |
| BL-core-a19-r1-resolve | PR83 | Major | OPEN | 3 Majors resolved into G1-G3 (+ nits G4-G7) |
| BL-PR89-r18-d01 | PR89 | Major | FIXED-UNVERIFIED | see reviews/PR89/r18-design.md M1 |
| BL-PR89-r18-d02 | PR89 | Major | FIXED-UNVERIFIED | see reviews/PR89/r18-design.md M2 |
| BL-PR89-r18-d03 | PR89 | Major | FIXED-UNVERIFIED | see reviews/PR89/r18-design.md M3 |
| BL-PR89-r18-d04 | PR89 | Major | FIXED-UNVERIFIED | see reviews/PR89/r18-design.md M4 |
| BL-PR89-r19-d01 | PR89 | Major | OPEN | reviews/PR89/r19-design.md M1 (M1-M3 reproduced by lead) |
| BL-PR89-r19-d02 | PR89 | Major | OPEN | reviews/PR89/r19-design.md M2 (M1-M3 reproduced by lead) |
| BL-PR89-r19-d03 | PR89 | Major | OPEN | reviews/PR89/r19-design.md M3 (M1-M3 reproduced by lead) |
| BL-PR89-r19-d04 | PR89 | Major | OPEN | reviews/PR89/r19-design.md M4 (M1-M3 reproduced by lead) |
| BL-PR89-r19-c01 | PR89 | Major | OPEN | reviews/PR89/r19-codebase.md M1 (duplicates design M4/M1/M2) |
| BL-PR89-r19-c02 | PR89 | Major | OPEN | reviews/PR89/r19-codebase.md M2 (duplicates design M4/M1/M2) |
| BL-PR89-r19-c03 | PR89 | Major | OPEN | reviews/PR89/r19-codebase.md M3 (duplicates design M4/M1/M2) |
| BL-core-a24-r1-05 | PR91 | Major | OPEN | marker regexes miss ruff: noqa, flake8: noqa, nosem |
| BL-core-a24-r3-02 | PR91 | Major | OPEN | nested pyproject rule bypassable by TOML spelling |
| BL-core-a24-r3-06 | PR91 | Major | OPEN | secret prefixes use \b, missed after escape letter or underscore |
| BL-core-a24-r3-07 | PR91 | Major | OPEN | 51 of 71 list lines have boilerplate unreviewed reason; reason gate nominal |
| PRH-r2-D1 | PRH | Major | OPEN | promise 2 (no step back) contradicted by _scrub second branch and step-6 fallback returning joined text |
| PRH-r2-D2 | PRH | Major | OPEN | longest-first sort misses partial overlap, equal length, mixed spelling domains; root condition deferred to PRH-c |
| PRH-r2-D4 | PRH | Major | OPEN | worst case 18 passes unmeasured and becomes refusal of legit large logs |
| PRHb6-r6-E2 | PRH | Major | OPEN | Issue 2: InputTooLarge on small input (7 of 3000 fuzz texts; 0 on main) |
| PRHb6-r6-E6 | PRH | Major | OPEN | Issue 4: 226 fuzz outputs keep a readable key or secret window with no spelled-out escape |
| PRHb8-r8-3 | PRH | Major | OPEN | r8 D3/M7: Issue 9 check_only and passes hill-climb not done; worst passes 16 of 24; perf multipliers 2.9-4.9 on hosti... |
| PRHb8-r8-8 | PRH | Major | OPEN | r8 M4/D8: soft-reading conflict check skips values shorter than 8 characters |
| PRHb8-r8-9 | PRH | Major | OPEN | r8 M5: mixed_keys drop in runmap |
| PRHb8-r8-10 | PRH | Major | OPEN | r8 M6/D9: duplicate 3,096-text generator (LCG and random.Random) and S311 noqa |
| PRHb11-r11-1 | PRH | Major | OPEN | r11 F4/F1: crash rule not at every catcher: approvals summary, injection check, tick step, evals, extract, k1b loop; ... |
| PRHb11-r11-2 | PRH | Major | OPEN | r11 F2: backslash-e inside a value readable near the end, short values, symbols (10 of 12 on head) |
| PRHb11-r11-3 | PRH | Major | OPEN | r11 F3: sibling containment at runmap 634 and 657 uses every held value; cut copy of held piece stays readable |
| Q8b-r1-M1 | Q8b | Major | OPEN | card path: key glued to e-mail/host leaves assignment value readable (87 vs 38 of 3000 on main) |
| Q8b-r1-C-F1 | Q8b | Major | OPEN | _named misses entry with both name and key |
| Q8b-r1-C-F2 | Q8b | Major | OPEN | Q8b |
| Q8bb6-r7-M1 | Q8b | Major | OPEN | digit-suffix credential keys (pass2, session2, --pass2) stay readable; auth0/oauth2 exceptions too wide |
| Q8bb6-r7-auth | Q8b | Major | OPEN | authorization scheme+token second word readable |
| Q8bb12-r13-6 | Q8b | Major | OPEN | r13 removing M195 hides a plantable fault for credential-key header names |
| BL-core-timing-r1-M1 | TIMING | Major | OPEN | reviews/timing-harness/result-r1-fa3f8c1.md M1 |
| BL-core-timing-r1-M2 | TIMING | Major | OPEN | reviews/timing-harness/result-r1-fa3f8c1.md M2 |
| BL-core-timing-r1-M3 | TIMING | Major | OPEN | reviews/timing-harness/result-r1-fa3f8c1.md M3 |
| BL-core-a18-w3-04 | UNASSIGNED | Major | OPEN | P6b1 no-training statement check itself not yet reviewed (reviewer got wrong slice from cloud) |

#### false or overstated documentation / CHANGELOG / wording claim (51 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-a21a-w2-09 | A21a | Major | OPEN | stale or private wording in three test docstrings ("lead report", "STANDING ORDERS 6d") |
| BL-core-a21a-w2-11 | A21a | Blocker | OPEN | tests/test_t1_meter_parallel.py (4 failing tests) fails the full suite; must move to A21b branch; reword docstrings |
| BL-core-a22-w2-01 | P0a | Major | OPEN | ticket row BN-4 says one test under 50 lines, builder report says 61 lines and 4 mutants, the file has 175 lines and ... |
| BL-core-a10a-w2-02 | P2a | Major | OPEN | guard probe INCONCLUSIVE only logs; ticket says refuse in pilot/prod; ProbeInconclusive unused |
| BL-core-a11a-w6-c02 | P2d | Major | OPEN | CHANGELOG:11 "an all-ASCII line behaves like a line with one non-ASCII letter" only true for lines holding a tab-like... |
| P3a2-3c-M3 | P3a-2 | Major | OPEN | CHANGELOG:15 quotes a message src no longer produces |
| P3a2-3d-D1 | P3a-2 | Major | OPEN | planted-fault test never runs the CHANGELOG message-form checker; "has" piece never checked |
| BL-core-a15-r1-02 | P5a | Major | OPEN | require_pinned_unidata runs after secrets make() in app.build; doc says first; test hides it |
| BL-core-a15-r2-04 | P5a | Major | OPEN | ticket P5a.md:360 says ten noqa sites / function-symbol keys; nine / guard strings |
| BL-core-peel-001 | PEEL-run-id | Major | OPEN | `Run.trigger_kind` accepts only event/schedule/user, so "webhook" fails validation (`models.py:94`, `agent_loop.py` h... |
| BL-core-a19-r1-03 | PR83 | Major | OPEN | six-word stage scan needs exemption rows for demo files and prose false positives; justify against ticket or narrow |
| BL-core-a19-r2-02 | PR83 | Major | OPEN | stages.py imports guard.runmap (no longer a leaf); docstring claims a pin that does not exist |
| BL-core-a2-w2-03 | PR89 | Major | OPEN | CHANGELOG/docstring say "exactly as before" but FIXTURE ERROR and judge() empty-id are always on; fixture_errors unnamed |
| BL-core-a2-w2-r13-14 | PR89 | Major | OPEN | CHANGELOG '10 s' bound not what tests check (M2) |
| BL-core-a2-w2-r13-15 | PR89 | Major | OPEN | mutants header Windows paragraph false (M3) |
| BL-PR89-r19-w01 | PR89 | Major | OPEN | reviews/PR89/r19-comprehension.md M1 (wording; reader would do something unsafe or wrong) |
| BL-PR89-r19-w02 | PR89 | Major | OPEN | reviews/PR89/r19-comprehension.md M2 (wording; reader would do something unsafe or wrong) |
| BL-PR89-r19-w03 | PR89 | Major | OPEN | reviews/PR89/r19-comprehension.md M3 (wording; reader would do something unsafe or wrong) |
| BL-PR89-r19-w04 | PR89 | Major | OPEN | reviews/PR89/r19-comprehension.md M4 (wording; reader would do something unsafe or wrong) |
| BL-PR89-r19-w05 | PR89 | Major | OPEN | reviews/PR89/r19-comprehension.md M5 (wording; reader would do something unsafe or wrong) |
| BL-PR89-r19-w06 | PR89 | Major | OPEN | reviews/PR89/r19-comprehension.md M6 (wording; reader would do something unsafe or wrong) |
| BL-PR89-r19-w07 | PR89 | Major | OPEN | reviews/PR89/r19-comprehension.md M7 (wording; reader would do something unsafe or wrong) |
| BL-PR89-r19-w08 | PR89 | Major | OPEN | reviews/PR89/r19-comprehension.md M8 (wording; reader would do something unsafe or wrong) |
| BL-PR89-r19-w09 | PR89 | Major | OPEN | reviews/PR89/r19-comprehension.md M9 (wording; reader would do something unsafe or wrong) |
| BL-core-pr89-r21-w01 | PR89 | Major | OPEN | reviews/PR89/r21-comprehension-full.md Major 1 |
| BL-core-pr89-r21-w02 | PR89 | Major | OPEN | reviews/PR89/r21-comprehension-full.md Major 2 |
| BL-core-pr89-r21-w03 | PR89 | Major | OPEN | reviews/PR89/r21-comprehension-full.md Major 3 |
| BL-core-pr89-r21-w04 | PR89 | Major | OPEN | reviews/PR89/r21-comprehension-full.md Major 4 |
| BL-core-a24-r2-07 | PR91 | Major | OPEN | CHANGELOG entry stale against the code and the list header |
| PRH-r2-R-M1 | PRH | Major | OPEN | W3 says _first_decoded NO change but main calls _decoded (regression) |
| PRHb6-r6-C3 | PRH | Major | OPEN | Issue 7: CHANGELOG piece claim wider than code; sampling gap above 132 chars; case-sensitive hex |
| PRHb8-r8-4 | PRH | Major | OPEN | r8 D4: SPACED_RUN_MIN_DISTINCT=6 undocumented, unmeasured in tests; ordinary-shape rows missing |
| PRHb8-r8-6 | PRH | Blocker | OPEN | r8 D6/B2: docs and docstrings state what the code does not keep (CHANGELOG line 8, _scrub, mutant count, passes 8 vs ... |
| PRHb9-r9-3 | PRH | Major | OPEN | r9 weak or missing mutants: mutant 114 killer asserts only out != text, group 5 rule has no mutant, docstring mutant ... |
| Q8a1b12-unread | Q8a-1 | Major | OPEN | batch 12 head 0e7da095: 164 allowance rows in the widened guard still reason UNREAD (UNREAD_LIMIT 164); no reason-pre... |
| Q8b-r2-3,9,10,11,12 | Q8b | Major | FIXED-UNVERIFIED | CHANGELOG-vs-LIMITS test, helper collectable on main, shadow card label, dead assertion, fence/colon rows/perf ratio |
| Q8bb8-r9-d1 | Q8b | Major | OPEN | r9 D9-1: CHANGELOG/LIMITS claim pins for `--pass2 a b` and `authorization=a b` that do not exist |
| Q8bb9-r10-6 | Q8b | Major | OPEN | r10 R10-5/F7: compass_key, overpass_key, encompass_key and similar readable (only bypass has second-word rule); COOKI... |
| Q8bb10-r11-1 | Q8b | Major | OPEN | r11 design M1/Minor2, codebase M2: controls table undone again: UNPLANTED_MAX 28->29, 29 controls unplanted, 7 false ... |
| Q8bb10-r11-2 | Q8b | Major | OPEN | r11 design M2, codebase M1: CHANGELOG claims without evidence: gate lines missing and not on the head, 179/182/183 mu... |
| Q8bb11-r12-5 | Q8b | Major | OPEN | r12 documents and builder gate files: invalid gate files; CHANGELOG and LIMITS claims wrong or unsupported; private n... |
| Q8bb13-r14-3 | Q8b | Major | OPEN | r14 codebase C2: card path for U+001C U+001D U+001E untested, CHANGELOG all five paths claim false for 3 of 8, stale ... |
| Q8c1b11-r11-4 | Q8c-1 | Major | OPEN | r11 M1/D11-6: builder notes row 72 overclaim (independent pins removed from changelog test); 22 pass-on-old rows need... |
| Q8c1b12-r12-5 | Q8c-1 | Major | OPEN | r12 M3: CHANGELOG.md:309 renewal rule differs from code (both lists renewed together) |
| Q8c1b13-r13-2 | Q8c-1 | Major | OPEN | r13 first renewal on 2026-12-12 is not green after the printed steps: B13 mutant survives, tests/test_policy_changelo... |
| Q8c1b14-r14-2 | Q8c-1 | Major | OPEN | r14 renewal plants (kinds alone, names alone, full renewal) have no mutant and notes claim a killing mutant that does... |
| BL-core-a21a-w2-01 | T1-T2 | Major | OPEN | builder full run NOT green: 4 failures in tests/test_t1_meter_parallel.py (known T1 finding, turn green with the Mete... |
| BL-core-a21a-w2-18 | T1-T2 | Major | OPEN | test tools/test_mutation_runner.py::test_the_runner_wires_pinned_so_another_failing_test_is_other_test is flaky on ba... |
| BL-core-a21a-w2-r2-01..05 (roll-up) | T1-T2 | Major | FIXED-UNVERIFIED | round-3 builder fixed rows w2-r2-01..05 (shared helper tests/pg_dsn.py, pin tests for NaN/negative/Infinity charges, ... |
| BL-core-flaky-r2-d01 | TIMING | Major | OPEN | hand-repeat note: deferred and its reason false; real ratios unmeasured |
| timing-r1-D-M1/C-M1 | TIMING | Major | OPEN | wait guard false Untimeable on tiny preempted batches |

#### concurrency, locks, timeouts, transactions (34 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-a10a-w2-01 | P2a | Blocker | OPEN | `limits stop` builds runtime store/signer/anchor/audit before the stopper store; stop refused when runtime store down... |
| BL-core-a10a-w2-03 | P2a | Major | OPEN | mutation Done gate (199/199) not met; 5 key mutants hand-run only; lock/deadlock/53300 mutants absent |
| BL-core-a10a-w2-07 | P2a | Major | OPEN | connection/timeouts limits hard-coded, not in config |
| BL-core-a10a-w2-08 | P2a | Major | OPEN | runbook lacks bootstrap, HD003 steps, lock key, exit 8 |
| BL-core-a11a-w6-c03 | P2d | Major | OPEN | views per line with a real mark about 15 not 8; traced about 11 s for a 4-column table with a backtick per row; measu... |
| BL-core-a11a-w7-B1 | P2d | Blocker | OPEN | reviews/PR77/round7-design.md B1 (REPRODUCED by lead; regression against main) |
| BL-core-a11a-w7-B2 | P2d | Blocker | OPEN | reviews/PR77/round7-design.md B2 (REPRODUCED by lead; regression against main) |
| BL-core-a11a-w7-cB1 | P2d | Blocker | OPEN | reviews/PR77/round7-codebase.md B1 (same root as design B1) |
| P3a2-3c-M4 | P3a-2 | Major | OPEN | transaction_timeout before commit: text says exit 2, code exit 3 |
| BL-core-a15-r2-03 | P5a | Major | OPEN | guard-counter lock test cannot fail on old code |
| BL-core-a17-w4-tst-01 | PR85 | Major | OPEN | compare lets a new unproven-origin site be labelled OPERATOR with a reason; FOREIGN_LIMIT never trips (gen:1231-1238)... |
| BL-core-a2-w2-r13-05 | PR89 | Major | OPEN | lock file name is a 64-bit offline guess check of the DSN (M3) |
| BL-core-a2-w2-r14-05 | PR89 | Major | OPEN | lock name untested for token-like ://, query, IPv6, bad port, no host, quoted host (M1) |
| BL-core-a2-w2-r14-13 | PR89 | Major | OPEN | Windows paragraph false (5 mutants), lock-name rule overstated, CHANGELOG terms undefined (M1-M3) |
| BL-core-a24-r1-fix1 | PR91 | Blocker | FIXED-UNVERIFIED | r1 B1,M2-M6 reported fixed by builder; unverified until a fresh pass |
| BL-core-a24-r2-06 | PR91 | Major | OPEN | CODEOWNERS misses the enforcing tests, pyproject.toml and uv.lock |
| BL-core-prh-plan-r1-b01 | PRH | Blocker | OPEN | reviews/PRH/plan-r1-readiness-full.md B1 |
| BL-core-prh-plan-r1-b02 | PRH | Blocker | OPEN | reviews/PRH/plan-r1-readiness-full.md B2 |
| PRHb6-r6-F1 | PRH | Blocker | OPEN | reviews/PRH/goldfish_review_report-r6.md Issue 1: encoded ESC plus encoded first letter hides a handed-out secret (CO... |
| PRHb7-r7-tests | PRH | Major | OPEN | r7 F3/F4/D4/D6-D8: mutant 100 equivalence unreproducible, tests that cannot fail, no withheld-share bound, 46 pass-on... |
| PRHb11-r11-6 | PRH | Major | OPEN | r11 F5: glued letter or mark before a spaced run starts no run; lookbehind blocks ignorable marks (design Major, code... |
| Q8a1b11-cD1 | Q8a-1 | Major | OPEN | reviews/Q8a-1/q8a1b11-codebase-r11.md D1: region/bucket not patterned for AWS and S3 settings; allowance reason and t... |
| BL-core-q8a-plan-r2-B1 | Q8a-plan | Blocker | FIXED-UNVERIFIED | reviews/Q8a/plan-r2.md clock default |
| Q8bb13-r14-2 | Q8b | Major | OPEN | r14 design D2 + codebase C1: 9 wall-clock tests without a planted fault, forbidden deferral third round; glued units ... |
| BL-core-q8b-plan-r1-B1 | Q8b-plan | Blocker | OPEN | reviews/Q8b/plan-r1-readiness.md B1 |
| BL-core-q8b-plan-r1-dB1 | Q8b-plan | Blocker | OPEN | reviews/Q8b/plan-r1-design.md B1 |
| Q8c1b9-r9-i1-2 | Q8c-1 | Major | OPEN | r9 Issue 1 (fixed day does not reach real-clock tests TODAY; "no result changes with the date" not shown) and Issue 2... |
| Q8c1b14-r14-1 | Q8c-1 | Major | OPEN | r14 renewal plants never run the notes check (blocking CI step); step 5 row count after closure rules unmeasured |
| BL-core-q8c-plan-r1-B1 | Q8c-plan | Blocker | OPEN | reviews/Q8c/plan-r1-design.md B1 and plan-r1-zoomout.md |
| BL-core-q8c-plan-r1-B2 | Q8c-plan | Blocker | OPEN | reviews/Q8c/plan-r1-design.md B2 and plan-r1-zoomout.md |
| BL-core-q8c-plan-r1-B3 | Q8c-plan | Blocker | OPEN | reviews/Q8c/plan-r1-design.md B3 and plan-r1-zoomout.md |
| BL-core-q8c-plan-r2-B1 | Q8c-plan | Blocker | OPEN | reviews/Q8c/plan-r2.md B1, B2 |
| BL-core-flaky-r2-d02 | TIMING | Major | OPEN | sibling wall-clock ceilings not fixed or named (test_k5_perf 30 s; test_k5_layers) |
| timing-r1-D-M2 | TIMING | Major | OPEN | real-clock tests not marked perf |

#### least-privilege and database grants / roles (23 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-a21a-w2-07 | A21a | Major | OPEN | contract test imports oracle/helpers from a sibling test module; move to tests/meter_support.py |
| BL-core-q8deps-F2b | MAIN-MISC | Major | OPEN | audit verify signs at start-up (cli.py:184-190, signer.py:79-90): a sign-free verifier identity is impossible (review... |
| BL-core-a10a-w2-06 | P2a | Major | OPEN | missing least-privilege behavioural tests (credential refs requested once, 53300, 40P01, S33, B9, INCONCLUSIVE) |
| BL-core-a11a-w3-02 | P2d | Major | OPEN | test_sep_1 never asserts the password is gone |
| BL-core-a11a-w5-t01 | P2d | Major | OPEN | test_marks_18 always prefixes the key with a space and skips the digit positions; `user\tAKIAIOSF\tODNN7EXAMPLE` and ... |
| BL-core-a5-w2-03 | P3a-2 | Major | OPEN | scope beyond frozen ticket (manifest, allow list, role-flag refusal, fixed timeouts, read-backs, pglast test, fixtures) |
| P3a2-3c-M1 | P3a-2 | Major | OPEN | promise row 1 says CI tests each role on the shipped files; ticket 7.7 test missing |
| P3a2-3c-M2 | P3a-2 | Major | OPEN | reduced matrix cannot show rows 1-2 for memberships, ownership, default rights, large objects, SECURITY DEFINER, C6/C... |
| P3a2-3c-N5 | P3a-2 | Major | OPEN | empty-ACL objects invisible to Q2 may hide O4/O8 from a hostile file |
| P3a2-45-gap | P3a-2 | Major | OPEN | commits 4/5 builder: full 37x13 matrix NOT built (18 effects x 6 carriers built), controls K2-K12 and carriers C3,C5,... |
| BL-core-a15-r2-01 | P5a | Major | OPEN | hard gate test_reverse_check_fails_90_percent missing (oracle blindness unproven) |
| BL-core-a2-w2-r13-04 | PR89 | Major | OPEN | password-word lookbehind skips sslpassword/dbpassword/PGPASSWORD (M2) |
| BL-core-a2-w2-r13-13 | PR89 | Major | OPEN | password-word lookbehind has no mutant and hides sslpassword/dbpassword (M1; same as r13-04) |
| BL-core-a2-w2-r14-02 | PR89 | Blocker | OPEN | password-derived bytes in the lock name: urlsplit puts a password containing / ? # into the path; hashed (B1) |
| BL-core-a2-w2-r14-03 | PR89 | Blocker | OPEN | key=value lock-name test passes for wrong reasons; quoted password holding host= text overwrites host (B2) |
| BL-core-a2-w2-r14-06 | PR89 | Major | OPEN | weak case 1350, property test can run zero cases, whole-literal fake passwords, read-before-size guard only patches r... |
| BL-core-a2-w2-r14-10 | PR89 | Blocker | OPEN | key=value DSN containing :// goes to urlsplit; password text in the lock name (B1) |
| BL-core-pr89-r21-d01 | PR89 | Major | OPEN | reviews/PR89/r21-design-full.md M1 second layer cuts the password out of caller-known text (lead reproduced) |
| PRH-r2-R-M2 | PRH | Major | OPEN | reader grammar 4.1: string sequence end rule, ESC inside string, strip_sequences scope, oracle |
| PRH-r2-R-M3..M9 | PRH | Major | OPEN | T5 sources not in ticket; tests not mapped to files/killers (35,36,31 unkillable?); cost gate four shapes undefined (... |
| Q8b-r1-F1 | Q8b | Major | OPEN | _named takes first of name/key: {"name":"db","key":"password","value":..} shows the secret |
| Q8bb6-r7-M2 | Q8b | Major | OPEN | drift test skips keys silently; plural flags (--secrets, --passwords) readable |
| Q8c-1-r2-fb2 | UNASSIGNED | Major | FIXED-UNVERIFIED | r2-M2 / r2-cb-M1: R17 claims_unverified set, copy-ready withheld, undelete/subkeys/byok-export shown "not yet checked... |

#### money, budget, cost, reserve and settle (14 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-a21a-w2-13 | A21a | Major | OPEN | T1 cap tested only on MemoryStore, not Postgres |
| BL-core-a21a-w2-14 | A21a | Major | OPEN | parallel harness cannot pass a choke-point fix (double charge); needs (reserve, settle) pair |
| BL-core-a21a-w2-16 | A21a | Major | OPEN | mutants miss year-in-month-key, Postgres agent filter and counters, both budgets over cap, NaN/negative/Infinity charges |
| BL-core-a21b-seed-01 | MAIN-MISC | Major | OPEN | meter accepts NaN, negative, Infinity charges into the ledger (money path); src untouched by A21a |
| BL-core-a10a-w2-05 | P2a | Major | OPEN | P4d money code inside the PR76 diff; true base and delta unstated |
| BL-core-a15-r1-04 | P5a | Major | OPEN | scan_keyset has no deadline (up to 8x3x262144 chars); reuse budget |
| BL-core-a15-r2-02 | P5a | Major | OPEN | test_every_active_row_has_teeth weaker than ticket (cap 40 vs 15, partial subjects) |
| BL-core-a18-w3-01 | PR86 | Major | OPEN | R1 no reserve-before/reconcile-after in any call path; cap is post-hoc; owner = P4b1/P4c; lead to confirm |
| BL-core-a18-w3-02 | PR86 | Major | OPEN | R2 agent_loop books nothing for unpriced/missing-usage/exhausted provider replies (money regression vs main); P4c-2 owns |
| PRH-r2-D3 | PRH | Major | OPEN | 1.25x cost limit unproven and not a gate; use pass counts + process time |
| PRHb8-r8-7 | PRH | Major | OPEN | r8 D7/M3: spaced-run cost unbounded and unmeasured; _sweep quadratic; no cap on runs |
| PRHb9-r9-1 | PRH | Major | OPEN | r9 spaced-run cost unmeasured and outside the work budget: run length not capped, 4 drops each full scans, spaced_spa... |
| Q8bb11-r12-3 | Q8b | Major | OPEN | r12 cost 2.07x main on 60000 chars; earlier figure measured on wrong commit; no ceiling; no literal prefilter |
| Q8bb12-r13-4 | Q8b | Major | OPEN | r13 CHANGELOG count of unplanted controls wrong (7 to 8 not 3 or 4), gate blind outside the list, cost median of thre... |

#### CI, build, scan and config guard (12 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-a5-w2-08 | P3a-2 | Major | OPEN | all SET refused and 5s/60s hard-coded: conflicts with P4d 0006 and P2a-1; not in validated config |
| BL-core-a15-r1-05 | P5a | Major | OPEN | REFUSAL_HANDLERS names functions that do not exist (loose lint exemption) |
| BL-core-a24-r1-04 | PR91 | Major | OPEN | NUL-byte skip runs before config/marker check |
| BL-core-a24-r1-06 | PR91 | Major | OPEN | scanner config names incomplete (ruff.toml, trivy-secret.yaml, bandit.yaml...), tool.ruff keys unchecked |
| BL-core-a24-r1-07 | PR91 | Major | OPEN | scan_allowlist.txt / scan_banned_extra.txt unguarded, "*" disables secret rules |
| BL-core-a24-r2-01 | PR91 | Blocker | OPEN | marker regexes are case-sensitive: `# NOQA`, `# NOSEC`, `# NOSEMGREP` are not hits |
| BL-core-a24-r2-02 | PR91 | Major | OPEN | marker set misses NOSONAR, lgtm, codeql, zizmor ignore, allowlist secret, NOPMD, checkov, tfsec, ruff disable/ignore ... |
| BL-core-a24-r2-03 | PR91 | Major | OPEN | nested non-root pyproject.toml with [tool.ruff]/[tool.bandit] not guarded; more scanner config names missing (sonar, ... |
| BL-core-a24-r2-04 | PR91 | Major | OPEN | NUL skip is an extension allowlist: .env, Dockerfile, .html and others escape secret scanning |
| BL-core-a24-r2-05 | PR91 | Major | OPEN | generator placeholder "NEW, needs a reviewed reason" is accepted by the scan |
| BL-core-a24-r3-05 | PR91 | Major | OPEN | symlink/non-regular config file skips the name check (is_file before check) |
| Q8a1b18-r19-6 | Q8a-1 | Major | OPEN | r19 D3/m1: configured names into stored records not tainted nor disclosed |

#### evidence gap (run missing, died, or unverified) (10 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-a11a-w4-ctl-01 | P2d | Major | OPEN | PR77 builder / runner hostile trial |
| BL-core-a5-w2-r3-03 (update) | P3a-2 | Major | OPEN | Evidence at head still not closed: builder log lacks Postgres/Python version, skip explanation, bandit output; indepe... |
| BL-core-a2-ci-01 (update) | PR89 | Major | FIXED-UNVERIFIED | PR89 branch core/mutation-runner-keywords, ORDER 235 |
| BL-core-a2-w2-r13-18 | PR89 | Major | OPEN | CodeQL alert 8 on bfce3d9 (tools/mutation_runner.py:604) |
| PRH-r2-D7 | PRH | Major | OPEN | rung table library row UNVERIFIED, no evidence |
| PRHb7-r7-fuzz9 | PRH | Major | OPEN | r7 evidence: 9 of 3096 random multi-cut texts leave an 8-character readable stretch of a made-up secret on head and c... |
| Q8bb6-r7-appendix | Q8b | Major | OPEN | ticket appendix A1-A5 and X1-X9 never run in any evidence |
| Q8bb9-r10-4 | Q8b | Major | OPEN | r10 R10-3/F5: "69 pass on old code each with a true reason" not true (evidence 58 fail, 47 pass ids; about 43 itemise... |
| Q8c1b11-r11-2 | Q8c-1 | Major | OPEN | r11 D11-2/D11-3/D11-9/M3: CI notes step red on first run (113 rows vs main), merge-commit diff, fetch fails private, ... |
| BL-core-flaky-r2-c01 | TIMING | Major | OPEN | evidence for a8c269c8 still running |

#### API, schema and contract design (4 rows)

| id | package | sev | ledger status | one-line summary |
|---|---|---|---|---|
| BL-core-peel-002 | PEEL-run-id | Major | FIXED-UNVERIFIED | A repeated `run_id` raises `StaleState` (typed refusal, before any write); the idempotent "return the existing run wh... |
| BL-core-a19-r1-02 | PR83 | Major | OPEN | TenantId/OrgId/etc. types used by no field; AST guard heuristic; wire to a real choke point or name a trigger |
| PRH-b-ticket | PRH | Major | OPEN | tickets/PRH-b-line-continuation-matching.md |
| Q8bb6-r7-cookie | Q8b | Major | OPEN | record key Cookie (capital) leaves any value readable (also on main) |

## 4. Apply script

File: `/home/user/build/ledger_triage_apply.py` (needs `ledger_parse.py`, `review_files.py`, `ledger_triage_rules.py` in the same folder). Default is a dry run that only prints counts. Nothing was applied.

```
python3 /home/user/build/ledger_triage_apply.py                      # dry run, counts only
python3 /home/user/build/ledger_triage_apply.py --apply              # R1 + the one manual row
python3 /home/user/build/ledger_triage_apply.py --apply --r2 --bm-clean   # also R2 and C1 (lead decision)
```

What it does with `--apply`: copies the ledger to `/home/user/build/ledger-backup-<UTC>.md`; changes only the status cell of the rows it lists (matched by line number, and it refuses a line whose text changed since the analysis); keeps the cell count of every line; re-reads the file and fails (restoring from the backup) if any line count or cell count differs, or any cell other than a listed status cell changed; prints counts by rule, package and old status. R1 sets `ACCEPTED-NIT (was <old>; rule R1 ...)`; C1 sets `FIXED-VERIFIED (was <old>; later clean round r<N>: <report>)`.
