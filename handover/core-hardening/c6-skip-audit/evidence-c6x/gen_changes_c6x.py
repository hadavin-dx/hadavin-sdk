"""Writes ../c6x-CHANGES.md. Usage: python3 -B -I gen_changes_c6x.py [verify_checks full_runs neg_changed neg_wrong scanned]; with no arguments the counts are read from the output files."""
import json, os, re, sys
E = os.path.dirname(os.path.abspath(__file__)) + "/"
def num(pat, f, d):
    try:
        m = re.search(pat, open(E + f, encoding="utf-8").read(), re.M)
        return int(m.group(1)) if m else d
    except OSError:
        return d
if len(sys.argv) == 6:
    C = dict(zip(["verify checks", "full runs of run_all.sh", "negative changed copies", "negative wrong copies", "scanned files"], map(int, sys.argv[1:])))
else:
    C = {"verify checks": num(r"^SUMMARY: (\d+) checks", "verify-c6x-output.txt", 0), "full runs of run_all.sh": open(E + "run-log.txt").read().count("run_all.sh start"),
         "negative changed copies": num(r"^SUMMARY: (\d+) copies", "neg-output.txt", 0), "negative wrong copies": num(r"^SUMMARY: \d+ copies, (\d+) wrong", "neg-output.txt", 0),
         "scanned files": num(r"^SCANNED (\d+) files", "scan-c6x-output.txt", 0)}
F = json.load(open(E + "c6v-findings.json"))
o = ["# c6x-CHANGES.md: what c6x changed against REPORT-c6w.md, finding by finding (written 2026-11-16, UTC; IST = UTC + 5:30)\n",
"FAILURES AND OPEN ITEMS FIRST (all mine, none hidden):",
"1. No EGM reviewer has read REPORT-c6x.md or the class 8 checks (verify_c6x_part5.py). Every 'checked' below means: my own scripts passed on my own text. The independent evidence runner has not run on c6x.",
"2. UNVERIFIED against the real files: the 104 old texts were checked only against the copy in evidence-c6x/tree/ (99 of 104 rows cannot be read in this repository). The builder who applies the rows must confirm each old text first.",
"3. G12 stays OPEN (the studio lead's gate). Nothing here approves it. Release note v18 dropping the words 'unless approved in writing' is NOT a decision; the report says so. The scope of G12 (four held items, twelve carve-out rows) is the report's own reading and no reviewer has confirmed it.",
"4. The 75 first failures 'D-late' of the c6w negative run: the onset was 19:44:35 UTC, after the unchanged copy V0 passed at 19:44:13; the live sheets were rewritten between them. I could not prove the cause from the c6w files alone, so c6x removes the cause (the input is pinned, steps-pinned and late-pinned, hashes in STEPS-PIN.txt and LATE-PIN.txt) and no longer counts a state-only failure as caught.",
"5. COUNT 314 against 313 (c6w review M-minor m1): the c6w COUNT included the unchanged copy V0. c6x counts changed copies only (V0 excluded); a copy equal to the report is reported NOOP and counts as wrong.",
"6a. v35 and v19 against v34 and v18 (c6w CHANGES 6a said 'equal'; REPORT-c6w line 75 said DIFFERENT): compared by script, evidence-c6x/compare-late-files-output.txt: all three pairs are DIFFERENT after the version number is changed. CHANGES of c6w was wrong; the report was right. The freeze stays at 2026-11-16T19:30:00Z (= 2026-11-17 01:00:00 IST).",
"6b. RUN COUNT: see the COUNT line below and run-log.txt (one line per run of run_all.sh, cap 2). Each run's exit lines are in run-log-exits.txt; if a run did not end clean, the report section 9 says so. The output file times against the report time are in order-check-output.txt.",
"7. NOT RUN: no commit, no push, no n8n run, no model call, no spend; the 104 rows are not applied; the lease re-smoke (TASK (5)) is not run. The old text of 99 rows is unread outside the copy in evidence-c6x/tree/.",
"",
"## Map A: each finding of review-c6v-design.md and review-c6v-naive.md (carried from c6w; the fix and its check still hold in c6x)\n",
"| id | the finding (short) | the fix in REPORT-c6x.md | the check |", "|---|---|---|---|"]
for fid, fnd, fix, chk in F:
    o.append("| %s | %s | %s | %s |" % (fid, fnd, fix, chk))
o += ["", "## Map B: each finding of the c6w reviews (review-c6w-design.md, review-c6w-naive.md, report-c6w-builder.md) and the late independent evidence on c6w\n",
"| id | the finding | the fix in c6x | the check |", "|---|---|---|---|"]
B = [
("c6w design M1", "the G12 hold lists differ (box, 1c-A, row 96)", "the four held items and the 76-word case are in the box item 6, row 96 and Table B", "C8-2, C8-3"),
("c6w design M2", "'in the box' claims were checked against box plus section 1c", "the class 8 checks read the start box alone (boxs)", "C8-1 to C8-8"),
("c6w design M3", "negative copies marked OK for the wrong reason (75 first failures D-late; the row 19 mutant)", "INTENT per copy; state-only failures never count; NOOP detection; row 19 mutant now edits the new-text cell", "neg-output.txt (no WRONG line), X-row19-G12-hold-removed-in-new-cell"),
("c6w design M4", "CHANGES 6a said equal, the report said DIFFERENT", "compared by script; both say DIFFERENT", "C8-11"),
("c6w design M5", "card line 3 against L-ONEDB", "card line 3 names n8n's own database only, no count; L-ONEDB states its scope", "C8-6"),
("c6w design m1", "COUNT 314 included V0", "changed copies only", "V13"),
("c6w design m2 to m6", "one crash point in the G12 test; silent L-LEASE no-op; typed line form; counts; word counts", "stated in the box and section 9, counted by script", "C8-8, C8-9, D-late"),
("c6w naive M1", "the box never says no reviewer has read it", "said in the first lines and in the box", "C8-1, C8-9"),
("c6w naive M2", "'newest at the check time' against the freeze", "'newest before the freeze' everywhere", "C8-14"),
("c6w naive M3", "card line 4 'other lease settings' not listed as held", "listed in item 6", "C8-2"),
("c6w naive M4", "only the approving G12 form in the box", "the three forms (approved, not approved, closed) in the box", "C8-4"),
("c6w naive M5", "two owner items about the take script without label, question, answer", "rows L-Q27, L-DELCRIT, L-KEYLINE in the box", "C8-5"),
("c6w naive M6", "'a sentence about the 45-second setting' has two meanings", "the box says the label and the carve-out rows; the 45-second sentence is defined", "C8-2 and the D-M2 checks"),
("c6w naive M7", "run_all.sh run 1 failure and the piece runs not stated", "section 0 and section 9 give a statement of each run", "C8-12"),
("c6w naive M8", "counts: seven stop steps, eleven gate rows, ten in CHANGES", "SEVEN STOP STEPS AND ELEVEN GATE ROWS, counted by script", "C8-8"),
("c6w naive M9", "the typed line names: literal or not", "the box says the names are chosen by the studio lead and no program reads the line", "C8-7"),
("c6w naive minors", "words lead, claim, A/B; scene 12; tonight; stale label", "defined in the box; dates added; stale label removed", "C8-13"),
("c6w builder report", "ORD:147 departure needs a lead yes or no", "question L-KEYLINE", "C8-5"),
("evidence runner 1", "five copies exit 0 with no failed check, and 07-card-87-words-first (first-copy-only edits of repeated numbers or phrases)", "the census holds the count of every copy of each card number and the gate phrase; one control per copy position, each with its intended check", "class 1 census, C8-15, X-*-copy* in neg-output.txt"),
("evidence runner 2", "an unrelated state-dependent failure counted as caught", "INTENT map; D-late and the other state checks count only where named; input pinned", "neg-output.txt"),
("evidence runner 3", "which build produced the report; output time against report time; run count", "section 9 names build_c6x.py and the run; order-check-output.txt; run-log.txt", "C8-12, V13"),
]
for r in B:
    o.append("| %s | %s | %s | %s |" % r)
o += ["", "## Counts (compared by the check script with the output files; a wrong number here fails V13)\n"]
for k, v in C.items():
    o.append("COUNT %s: %d" % (k, v))
o += ["", "## Which branch holds what, and who read what",
"- The report, this file, the scripts and the outputs are in handover/core-hardening/c6-skip-audit/ and its evidence-c6x/ folder (branch cloud/core-hardening). Nothing is committed by me. The 99 demo-file rows concern branch cloud/flows-audit; the 5 rows 70, 71, 72, 90 and 91 concern branch cloud/core-hardening.",
"- review-c6w-design.md, review-c6w-naive.md and review-c6w-evidence.md read REPORT-c6w.md only. No reviewer has read c6x.", "",
"## Files changed or made in c6x",
"REPORT-c6x.md, REPORT-c6x-TABLE.md, REPORT-c6x-COVERAGE.md, c6x-CHANGES.md, checkpoint-c6x.md, evidence-c6x/ (build_c6x.py, assemble_c6x.py, verify-c6x.py, verify_c6x_part2 to part5, neg_*.py, scan_c6x.py, gen_changes_c6x.py, run_all.sh, static-checks.sh, census-c6x.json, run-log.txt, steps-pinned, late-pinned, outputs). REPORT-c6w.md, c6w-CHANGES.md and evidence-c6w/ were not edited."]
open(E + "../c6x-CHANGES.md", "w", encoding="utf-8").write("\n".join(o) + "\n")
print(C)
