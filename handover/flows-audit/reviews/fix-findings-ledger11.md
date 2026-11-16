# fix-findings-ledger11 (round 11, non-security path): fixes for reviews/findings-ledger-reader-r10.md
Fixer: the audit (cloud session flows-audit). Static work only: nothing ran, no network, made-up data. Edited: FINDINGS.md, LEDGER-ROWS.md; new: reviews/ledger-history-cells.md (the archive, original fix cells word for word) and this file. No severity, no status and no count changed (45 rows, 5 Blocker, 5 Major, 35 Nit, BEFORE 11, AFTER 34). Reviewer words were checked against the files; two reviewer claims are partly wrong (findings 1 and 7, below).

## Status per finding (fixed / contested / needs lead)
1. FIXED, reviewer partly wrong: Q31 item 11 DOES ask F-003 (its title is 'WHO APPLIES F-003, F-031 AND F-007' and its rows cell lists F-003). The wrong text was ours: F-003 cell, FINDINGS F:195 (5). Corrected in both places; the F-007 cell sentence now says item 11 asks who applies the text of F-003, F-031 and F-007. QUESTIONS.md needs no change.
2. FIXED: 'Wed 18 Nov 06:00Z is the audit's proposal borrowed from Q30 item 2 (names F-007 and F-031 only)' written at the causes bullet, the F-003 bullet, the table-of-inputs row 10 and the F-003 cell (ORDERS.md line 171 read: item 2 names F-031 and F-007 only).
3. FIXED in our text, NEEDS LEAD for the question itself: new decision-table row 'NEW, proposed' (runner, hours, slot for F-011 fix A, due Tue 17 Nov 03:00Z); the F-011 cell now has one reading of timing (settings at the first n8n start, RUNBOOK step 7; the three runs need their own slot; the table of inputs row 4 is consistent). QUESTIONS.md is not ours to edit; proposed text is below.
4. FIXED in our text, NEEDS LEAD for two lines: T7b and the kill run now have literal lines (RESULT T7b PASS, RESULT K1 PASS, mf.py sets no exit code, read in mf.py). UNVERIFIED and NEEDS LEAD: T7b as written scans a SQLite data folder, so on Postgres it must be adapted (who adapts it); no import command exists in the tree (TAKE-CHECKLIST GO row 7 says so), so the import pass is the audit's proposal only (exit 0 for 4 files, then 4 workflows listed).
5. FIXED: F-002 cell says item 16 default is NO (not written early), says what a failed T19 costs without F-002b, and the older wrong sentence is recorded in the archive.
6. FIXED: wait value is named by item 25 (Tue 06:00Z); item 50 asks the count command and that the value is written into the test log (Wed 05:45Z); same fix in WEDNESDAY CLOCK 'inputs for F-002'.
7. FIXED, reviewer right: item 21 asks only Blocker or Major; item 26 asks who closes the rows. Corrected in the causes bullet and in the F-037 cell.
8. FIXED: top of WEDNESDAY CLOCK now says every Wednesday time assumes Tuesday GO; after a NO-GO they move to Thu 19 Nov (item 84 default: re-pin repeats on Wed 18 Nov; the audit's reading, lead to confirm) and the latest take day is Mon 23 Nov 12:00Z; item 85 applies only on the last slip day.
9. FIXED: seven GO test rows are a table under the TUESDAY paragraph; F:195 (6) points to it; 'clear rows 6 and 7 (rows 1 to 5 still must pass)' written; 'seventh counted row' became 'one more counted ledger row (making seven)'; 'Each of the seven' became 'Each of these seven ledger rows'; bare 'item n' in that paragraph became 'Q31 item n'.
10. FIXED: F-029 now has a positive control for each name (PLACEHOLDER: mf-recovery and mf-sub-crm-mail; SUB_WORKFLOW_ID: mf-form, mf-hook, mf-recovery; PG_CREDENTIAL_ID: all four; SMTP_CREDENTIAL_ID: mf-recovery and mf-sub-crm-mail; read by grep -lF over real-v5 on 2026-11-16, not run on the patched copy).
11. FIXED: counts caption says the re-pin is 12 pieces of work (11 BEFORE rows plus the F-004 patch); the counts stay BEFORE 11, AFTER 34.
12. FIXED: new top line 'WHO ANSWERS THE Q31 QUESTIONS, WHERE IT IS RECORDED, WHO MAY BE SECOND READER' (the studio lead; ORDERS.md ANSWER blocks; a fresh review agent session as second reader; whether it counts as a 'person' stays UNANSWERED).
13. FIXED with a stated limit: F-002, F-003 and F-011 fix cells restructured: SUMMARY, numbered who/what/by-when/artifact list, commands and pass lines, pointer; history moved word for word to reviews/ledger-history-cells.md (each original cell appears there in full, plus a real table and the corrections). Cell sizes in characters: F-002 23,023 to about 20,750; F-003 9,986 to 8,930; F-011 10,388 to 11,855 (F-011 grew: the literal pass line and the who list were added). THE F-002 CELL IS STILL LONG because the three test commands (T19, T20, T21 with its method, about 11,000 characters) are what a closer runs and may not move. Nested brackets were removed from the who/by-when part. If the reviewer wants the commands in a separate file too, that is a further move (needs lead).
Nits: N1 FIXED (T1 became T19, T20 and T21); N2 FIXED (FIX-PLAN item 3 step 7, two places); N3 FIXED (RUNBOOK step 1); N4 FIXED (item 32 row added to the decision table); N5 FIXED ('15 different ways by the N7-7 count (UNVERIFIED, not recounted)', both files); N6 FIXED (F-001 ledger prefix says FIXED-UNVERIFIED names only the unrun gate; the move to FIXED-VERIFIED is the audit's proposal); N7 FIXED (F-008 pass line has check (4) for saveManualExecutions); N8 CHECKED, cites correct (ORDERS.md line 156 item 9 reads as cited; no change); N9 FIXED (line numbers inside text replaced by heading names). Terms: bare 'item' in the TUESDAY paragraph became 'Q31 item'; 'wait up to 30 minutes' became 'grace period of up to 30 minutes' in FINDINGS.md (defined in the new top line). NEEDS LEAD: QUESTIONS.md items 50, 54, 59 and 82 still say 'wait up to 30 minutes'; the audit does not edit that file.

## Proposed new Q31 question (planned by the audit, lead to confirm; not in QUESTIONS.md)
F-011 FIX A, WHO RUNS IT: if the answer to item 10 (a) is 'fix A', who runs the three runs (T7b on Postgres, the import test of the 4 flows, one kill run), in which hours, and in which slot (inside RUNBOOK step 7 or a separate slot before Tue 17 Nov 14:00Z (19:30 IST))? Answer by Tue 17 Nov 03:00Z (08:30 IST), with item 10 (a). If unanswered: no runner is named, fix A does not run, and GO row 7 is the automatic NO-GO.
Also needed from the lead: the exact import-test lines; who adapts T7b to Postgres; confirmation that the kill run is K1.

## Comparison script (python3 -I, run from this folder) and its output
```
import re, sys
f, l = sys.argv[1], sys.argv[2]
F = {}
for ln in open(f, encoding="utf-8"):
    m = re.match(r"\| (F-\d+) \| ", ln)
    if m:
        F[m.group(1)] = ln.rstrip("\n").split(" | ")
L = {}
for ln in open(l, encoding="utf-8"):
    m = re.match(r"\| (F-\d+) \| ", ln)
    if m:
        L[m.group(1)] = ln.rstrip("\n").split(" | ")
diff = 0
for i in F:
    a, b = F[i], L.get(i)
    if b is None or len(a) != 10 or len(b) != 9:
        print("SHAPE", i, len(a), len(b) if b else None); diff += 1; continue
    fix_l = b[6]
    if i in ("F-001", "F-013"):
        fix_l = fix_l.split(a[7][:30], 1)
        fix_l = (a[7][:30] + fix_l[1]) if len(fix_l) == 2 else b[6]
    sev = a[1].split()[0] == b[2].split()[0]
    stat = a[9].split()[0] == b[5].split()[0]
    bold = re.match(r"\*\*(.+?)\*\*", a[6])
    summ = (bold.group(1) in b[4]) if bold else True
    fix = fix_l == a[7]
    if not (sev and stat and summ and fix):
        diff += 1; print("DIFF", i, "sev", sev, "status", stat, "summary", summ, "fix", fix)
print(len(F), len(L), "differences:", diff)
```

Output and the five checks:
```
$ python3 -I compare.py FINDINGS.md LEDGER-ROWS.md
45 45 differences: 0
$ python3 -I tools/count_findings.py
rows 45 unique 45
| Blocker | 5 | 0 | 5 |
| Major | 5 | 0 | 5 |
| Nit | 1 | 34 | 35 |
| all | 11 | 34 | 45 |
sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
$ tools/check_refs.py
PASS 5176 references
$ tools/check_names.py
PASS 655 rows
$ tools/check_secrets.py
PASS 0 hits in 2664 files
$ ruff format --check .
812 files already formatted
$ grep -n '^- \*\*WEDNESDAY CLOCK (one source' FINDINGS.md
209:- **WEDNESDAY CLOCK (one source: every row and every Q31 item poin
```
