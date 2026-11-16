# fix-f1-r2: CLAIMS-TABLE round 2 fixes (queue item F1), 2026-11-16

What failed or stayed unverified (first):
- Nothing ran; static reading only. I did not re-check the other verdicts, the relayed numbers (lane3, V7), the built flow JSON, FINDINGS.md or the patches.
- Could not read fix F-01 (named in AGENT-SCOPE-DO-AND-DONT.md:20 as in review-codebase-1.md; that file is not in this checkout). Row for ONS:103/:112 follows the lead's ORDER 017 and flags the conflict.
- Two judgement calls: A-097 moved to OVERSTATED (reviewer offered UNTRACED or OVERSTATED); B-045/B-046 moved to UNTRACED (reviewer M1, confirmed). Checks P4a (= P3), P4b, P4c are new and nobody has run them.
- The 12-column tables are wide; the lead may want a narrower view.
- Row numbers changed (grouped by file); the "was" number maps to round 1.
- I did not run EGM steps myself (no skill invocation from here); round 2 is the last allowed round, so the lead decides on a further check.

Each reviewer finding, verified before changing
- Blocker, no first-step / unclear who decides / labels unexplained: new "Start here" block (failure list, who decides, order of work, glossary of every label, check-before-filming lists). Checked: Q4-Q8 text against ORDERS.md ORDER 013; K-labels against mf.py:158,164 and V7-NUMBERS-lead-read.md; T-labels against lane rows. T17, T19, M1 are only named in the files, so the glossary says so.
- Major, no file / done column, not grouped by file, truncated words: tables rebuilt with columns file to edit, line, ids (was row), full current sentence (lane quote), why, needs, replace with, other branch, note, done; index by file added.
- Major, conflicts: rows was 12/13/21 (R:39, :62, :88 vs :50) and was 3/8 (R:33 time cell vs caption): they edit different cells or lines once row 12 lost :39; winner stated in the table note and in the rows' notes.
- Major, instructions in replacement cells: moved to the note column (rows was 3, 7, 13, 25, 26, 27, 11); second branch given for P1 rows (was 9, 10, 23, 28) and P2 rows (was 6, 16). P1 other branch checked against SUB flow facts: mail step ended done leads to MarkDone, reply verdict "new", no alert.
- Misreads fixed: D3 default (the alert mail on screen still says "A person decides"); was row 1 (scenes 6 to 10 also stand-ins); was row 20 (narrowed to our own CRM account); was rows 25/26 (lane3/V7 labels kept off screen text); 13 vs 12 minutes (two different events); was rows 55/52 (marked "read in the files, not run"); was rows 48/58/62 and 14 (marked relayed).
- Codebase M1 (row 40): confirmed by reading AGENT-SCOPE-DO-AND-DONT.md:12-16 and DECISION-one-store.md:9; verdict now UNTRACED in lane B, CLAIMS-TABLE and lanes13/claims-B.md.
- M2: added rows for B-189, B-024 and a note row for B-078. M3: A-011 and A-090 pipe signs fixed (grep for a row whose pipe count is not 8 now finds none); the false note "inner pipes none in lane A" corrected.
- Minor: V7 note (summary file exists; raw absent) fixed; A-081 now needs D1, D2; B-168 272 s marked relayed; B-054 narrowed (V5-README.md:17 names K1, not T1); A-097 verdict.
- Naive-reader nits: 79 vs 76 explained; mixed row numbers/ids now "ids (was row)"; "by script" names the script (below); queue code explained in the glossary.
- ORDER 017 local facts added to Start here, the checks list and the tables: HubSpot id check P4a (= P3; ID-VID-CHECK.md), "one database" P4b (new row for DECISION-one-store.md:14), clean-up P4c (new rows for ONS:103/:112 and the old "archives" sentences B-017, B-067, B-091), plus row for B-051 and A-012 (P4a).
- Also found: steps 4 and 6 of the owner steps are not named as done in FACTS-ALREADY-DONE.md; round 1 said "treated as done". Corrected; a missing HubSpot property hadavin_label would make the CRM step fail.

Recount (by script, run on the final CLAIMS-TABLE.md and the two lane files)
Result: 327 claims (A 97, B 226 + X 4 = 230): SUPPORTED 114, RELAYED-ONLY 69, OVERSTATED 49, UNSUPPORTED 25, UNTRACED 70. Lane A: 34/24/19/13/7. Lane B: 80/45/30/12/63. Tables: 89 claims in 77 rows (40 + 37). Every row has 7 cells and 8 pipe signs.

Files changed: CLAIMS-TABLE.md, lanes13/claims-A.md, lanes13/claims-B.md, fix-f1-r2.md. No other file was edited.

Script text (count.py; run `python3 count.py CLAIMS-TABLE.md`):
```python
import re,sys,collections
V=["SUPPORTED ONLY BY RELAYED NUMBER","SUPPORTED","OVERSTATED","UNSUPPORTED","UNTRACED"]
def count(path, start=None):
    c=collections.Counter(); lane=collections.Counter(); bad=[]; ids=[]
    txt=open(path,encoding='utf-8').read().split('\n')
    for l in txt:
        m=re.match(r'\| (A-\d+|B-\d+|X-\d) \|',l)
        if not m: continue
        cells=l.strip().strip('|').split(' | ')
        if len(cells)!=7: bad.append((m.group(1),len(cells))); 
        v=cells[5] if len(cells)==7 else None
        if v is None: continue
        for k in V:
            if v.startswith(k): c[k]+=1; lane[m.group(1)[0]]+=1; break
        else: bad.append((m.group(1),'noverdict',v[:30]))
        ids.append(m.group(1))
    return c,lane,bad,ids
if __name__=='__main__':
    c,l,b,ids=count(sys.argv[1]); print(dict(c),dict(l),b,len(ids),len(set(ids)))
```
