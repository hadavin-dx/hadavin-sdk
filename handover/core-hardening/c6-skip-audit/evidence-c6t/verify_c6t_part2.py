# part 2 of verify-c6t.py: executed statement by statement so that one crash is one FAIL, not the end of the run
# 14 c6q content checks
import glob
bylead = {r["i"]: r for r in rows}
boxs = full[full.index("## Start here"):full.index("## 0. Failures")]   # the short start box (order, words, labels)
sec1c = full[full.index("## 1c."):full.index("## 2. Numbers")]   # the detail moved out of it
box = boxs + "\n" + sec1c   # the presence checks of c6s look in both
intro = box[:box.index("WORDS YOU NEED (")]
check("no row is NOT FILMABLE", not nofilm, nofilm)
# card lines, recomputed from rows 13 and 14
W = []
Q = []
for k in (13, 14):
    for q in re.findall(r'spoken: "([^"]*)"', bylead[k]["new"]):
        Q.append(q)
        W.append(len(q.split()))
NW = sum(W)
sec_ = NW / 150 * 60
bud = int(sec_ // 5) * 5 + (5 if int(sec_ // 5) * 5 < sec_ - 1e-9 else 0)
check("rows 13+14 hold 4 spoken lines of %d words" % NW, len(W) == 4 and NW > 0, W)
check("box prints all four card lines exactly as the rows have them and the total (%d words, about %d s, budget %d s)" % (NW, round(sec_), bud),
      all(("'%s'" % q) in box for q in Q) and ("Total %d words, about %d s, budget %d s" % (NW, round(sec_), bud)) in box, "")
r11 = bylead[11]["new"]
check("row 11 states the same words, seconds, budget and total (about %d s)" % (150 + bud), ("%d words" % NW) in r11 and ("%d s" % round(sec_)) in r11 and ("closing card %d s" % bud) in r11 and ("about %d s in all" % (150 + bud)) in r11 and "EST NOT MEASURED" in r11, r11[:120])
# table of lengths recomputed from the quoted sentences
ql = [l for l in box.split("\n") if l.startswith("| L-LEASE |") and "1 = '" in l]
m1 = re.search(r"1 = '([^']*)'", ql[0]) if ql else None
m2 = re.search(r"2 = '([^']*)' \(40 words", ql[0]) if ql else None
cl = [l for l in txt if l.startswith("| L-CARDLEN | studio lead")]
mb = re.search(r"line 1 '(.*?)' line 2 '(.*?)' line 3 '(.*?)' line 4 '(.*?)' \(\d+ words", cl[0]) if cl else None
ok = bool(m1 and m2 and mb)
tab_calc = []
if ok:
    w = lambda x: len(x.split())
    a_rest = W[1] + W[2] + W[3]
    b_rest = w(mb.group(2)) + w(mb.group(3)) + w(mb.group(4))
    add = {"none": 0, "1": w(m1.group(1)), "2": w(m2.group(1))}
    for k in ("none", "1", "2"):
        for ln, l1, rest in (("(a)", W[0], a_rest), ("(b)", w(mb.group(1)), b_rest)):
            ww = l1 + add[k] + rest   # ONE construction: the lease sentence is added to line 1; lines 2 to 4 are not touched
            s2 = ww / 150 * 60
            b2 = int(s2 // 5) * 5 + (5 if int(s2 // 5) * 5 < s2 - 1e-9 else 0)
            tab_calc.append((k, ln, ww, "%.1f" % s2, b2, 150 + b2))
boxrows = []
for l in box.split("\n"):
    mm = re.match(r"^\| (none|1|2)[^|]* \| \((a|b)\)[^|]* \| (\d+) \| ([\d.]+) \| (\d+) s \| about (\d+) s \|$", l)
    if mm:
        boxrows.append((mm.group(1), "(%s)" % mm.group(2), int(mm.group(3)), mm.group(4), int(mm.group(5)), int(mm.group(6))))
check("one construction in the length table: no 24-word rewrite of line 1 anywhere (c6q design review M-F)", "B_L1_R1" not in open(os.path.dirname(os.path.abspath(__file__)) + "/build_c6r_text.py").read() and "24-word" not in full and "24 words" not in box, "")
check("table of lengths in the box (6 rows) equals the recomputation from the quoted card lines and lease sentences", ok and boxrows == tab_calc and len(boxrows) == 6, (boxrows[:2], tab_calc[:2]))
check("answer 2 replaces answer 1: net +15 words and no 'add 16' wording", ok and (W[0] + len(m2.group(1).split())) - (W[0] + len(m1.group(1).split())) == 15 and "net +15 words" in full and not re.search(r"\+16 s|add 16|adds 16", full), "")
# questions and L-POST
check("L-POST exists in the box table and in section 3, with a default", any(l.startswith("| L-POST |") for l in box.split("\n")) and any(l.startswith("| L-POST (new in c6q)") for l in txt))
check("rows 11, 13, 14(not), 21 tie to L-POST and L-LEASE (13, 21) and the tied column lists them", all("L-POST" in bylead[k]["st"] for k in (11, 13, 21)) and all("L-LEASE" in bylead[k]["st"] for k in (13, 21)), "")
ll = [l for l in txt if l.startswith("| L-LEASE | studio lead")]
need = ["ORD:230", "ORD:186", "Q22 (c)", "NONE (the default)", "ANSWER 1", "ANSWER 2", "NOT TO BE SPOKEN AS FACT BEFORE C-9 PART 2", "WHAT 'NONE' CLAIMS, HONESTLY", "G12", "LRN:33", "LREP:80", "RECOMMENDATION", "REPLACES", "claim", "again"]
check("section 3 L-LEASE: newest word, honest claim of 'none', G12 open, reading-2 facts not to be spoken, replacement, recommendation", len(ll) == 1 and all(x in ll[0] for x in need), [x for x in need if not ll or x not in ll[0]])
check("L-LEASE definition is the true one (takeover only; repeat refused while the row exists)", "claim the contact again" in box and "may claim a contact that is not finished again" in full and "NOT the time during which a repeat send is recognised" in full)
check("rows 17 and 81 say 'may' about the 45 s setting", "may be named" in bylead[81]["new"] and "neither 45 s nor 120 s" in bylead[81]["new"])
check("rows 13 and 21 carry the plain statement and no 45-second sentence by default", "within 45 seconds" not in bylead[13]["new"] and "within 45" not in bylead[21]["new"] and "processed once" in bylead[13]["new"] and "processed once" in bylead[21]["new"])
# C-10b, no-take line
c10b = [l for l in txt if l.startswith("| C-10b |")]
check("C-10b: pass and fail cells agree (all of (a), (b) and (c) shown / any not shown)", len(c10b) == 1 and "all of (a), (b) and (c) are shown with line numbers" in c10b[0] and "any of (a), (b), (c) not shown" in c10b[0], "")
check("the 'no take on Mon 23 Nov unless (a), (b) and (c)' line is in the box once, with 18:04 UTC = 23:34 IST once as a plan fact", box.count("applies the strictest reading of your answer Q27") == 1 and "MY ASSUMPTION" in box and "OWNER-OPEN" in box and box.count("18:04 UTC = 23:34 IST") == 1 and "plan fact" in box, "")
check("no 'Tuesday evening' or 'Tue evening' inference", not re.search(r"(?i)tue(sday)?\.? evening", full), "")
bad1051 = [i + 1 for i, l in enumerate(txt) if "1051" in l and "UNVERIFIED" not in l]
check("every line that names plan line 1051 says it is UNVERIFIED", not bad1051, bad1051)
check("departure from ORD:147 stated in section 0, in the L-DEL row and in row 8", "DEPARTURE FROM ORD:147" in full.split("## 1.")[0] and any(l.startswith("| L-DEL") and "DEPARTURE FROM ORD:147" in l for l in txt) and "DEPARTURE FROM ORD:147" in bylead[8]["why"], "")
check("fresh container wording (ORD:146) in row 8, C-9 and the box", "fresh database container" in bylead[8]["new"] and "ORD:146" in bylead[8]["why"] and any(l.startswith("| C-9 |") and "fresh container" in l for l in txt) and "fresh" in box)
# L-SCENES, stale words
check("L-SCENES appears only in coverage lines (section 8), never in a live table or row", all("L-SCENES" not in l for l in txt[:next((i for i, x in enumerate(txt) if x.startswith("COVERAGE OF THE c6p REVIEWS")), len(txt))]) , "")
# row 6 items, row 90, report words in new texts
r6 = bylead[6]["new"]
check("row 6 item 11 has no 'needs n8n and is not run yet'", "needs n8n and is not run yet" not in r6)
i15 = r6[r6.index("15. SECOND LEAK SCAN"):r6.index("16. AFTER THE TAKE")]
check("row 6 item 15 says what the second scan searches for (real key values read from the key file, not printed, counts only)", all(x in i15 for x in ["the real value of the mail account's password", "the real value of the customer-list key", "pattern file that exists only in memory or through standard input", "never on a command line", "never saved to disk", "made-up names", "hit counts only"]), "")
nn = [i + 1 for i, l in enumerate(txt) if re.search(r"\b(103|75|71) words", l) and not re.search(r"c6[nop]|history|was ", l)]
check("no stale card word count (103, 75, 71) outside history lines", not nn, nn[:3])
i13 = r6[r6.index("13. REPEAT-SEND CHECK"):r6.index("14. GATE")]
check("row 6 item 13: the 30 s rule applies only if the card or caption carries the 45-second limit", "If the closing card or the scene 3 caption says that the claim holds only within 45 seconds" in i13 and "If neither the card nor the caption says so" in i13, "")
check("row 6 keeps items 11 to 16, no blank, no builder note", all(("%d. " % n) in r6 for n in range(11, 17)) and "______" not in r6 and "SESSION-HANDOFF" not in r6)
check("row 6 item 16 does not claim that deleting erases the data", "NOT verified" in r6.split("16. AFTER THE TAKE")[1] and not re.search(r"(?i)erases? (the|all) (data|contact)|deletes? the data", r6.split("16. AFTER THE TAKE")[1]))
r90 = bylead[90]["new"]
check("row 90 new text ends with the database n8n (so 'owned by' attaches to it) and has no 'third place'", r90.rstrip().endswith("database `n8n`") and not r90.rstrip().endswith("own state") and "third place" not in full.lower().replace("'third place' removed", ""), r90[-80:])
check("row 91 says the stage journal and some bookkeeping files stay files", "stay files" in bylead[91]["new"])
r8 = bylead[8]["new"]
check("row 8 has 18:04 UTC = 23:34 IST, a plan fact that moves, (a)(b)(c), UNVERIFIED, STOP", "18:04 UTC = 23:34 IST" in r8 and "plan fact" in r8 and all(x in r8 for x in ["(a)", "(b)", "(c)", "UNVERIFIED", "STOP", "EVERY line"]), "")
check("row 76 is tagged design intent, rows 25, 37, 38 say 'stored' not 'delivered'", "design intent" in bylead[76]["new"] and all("stored by the test mailbox" in bylead[k]["new"] and "after the mail was delivered" not in bylead[k]["new"] for k in (25, 37, 38)), "")
bad144 = [r["i"] for r in rows if re.search(r"144\.3", r["new"]) and not re.search(r"144\.3[^|]{0,120}n8n (coming |came )?back up|from n8n", r["new"])]
check("every new text with 144.3 labels it as from n8n coming back up", not bad144, bad144)
rn = [(r["i"], m.group(0)) for r in rows for m in re.finditer(r"\brows? \d+", r["new"])]
check("no 'row N' reference in any new text", not rn, rn[:5])
ac = [r["i"] for r in rows if re.search(r"\baccepted\b", r["new"])]
check("no 'accepted' exit slip in any new text", not ac, ac)
bl = [r["i"] for r in rows if re.search(r"(?<!studio )(?<!Studio )\blead\b(?!er)", re.sub(r"[Aa] lead sent twice with the same id is processed once", "", r["new"]))]
check("no bare 'lead' in new texts (the one decision sentence excepted)", not bl, bl)
# 5a
vis = sorted(r["i"] for r in rows if not r["view"].startswith("Nothing") and ("VIDEO-RUNSHEET" in r["f"] or "PAGE-STATEMENTS" in r["f"]))
a5 = full[full.index("5a. WHAT CHANGES"):full.index("5b. THE CLOSING CARD")]
got5 = [int(m.group(1)) for m in re.finditer(r"^\| (\d+) \| (?:run sheet|page statements), line", a5, re.M)]
check("5a lists exactly the %d viewer-visible run-sheet and page rows" % len(vis), got5 == vis and any("PAGE-STATEMENTS" in bylead[k]["f"] for k in got5), (len(got5), len(vis)))
check("5a text equals each row's own 'what the viewer sees' cell", all(("| %d | " % k) in a5 and bylead[k]["view"] in a5 for k in vis))
# owner sheets
cs = rd(H + "/handover/core-hardening/c6-skip-audit/evidence-c6t/static-checks-output.txt")
ct = re.search(r"check time \(UTC\): (\S+)", cs).group(1)
vs = sorted(int(m.group(1)) for f in glob.glob(STEPS + "/OWNER-SHEET-v*.md") for m in [re.search(r"OWNER-SHEET-v(\d+)", f)] if m)
check("report names the check time %s and the newest sheet version on disk (v%s)" % (ct, vs[-1] if vs else "?"), bool(vs) and ("v%d" % vs[-1]) in full and ct[11:19] in full and ct[:10] in full, vs[-3:])
import datetime
ct_dt = datetime.datetime.strptime(ct, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
late = [os.path.basename(f) for f in glob.glob(STEPS + "/OWNER-SHEET-v*.md") if os.path.getmtime(f) > ct_dt]
check("no owner sheet changed after the stated check time (C-10c is current)", not late, late)
check("no claim that v25 or v26 is the newest", not re.search(r"(?i)newest[^.|]{0,60}v2[56]\b(?!-SOURCE\b)", full), "")
NEWV0 = max(int(re.search(r"-v(\d+)-", f).group(1)) for f in glob.glob(STEPS + "/OWNER-SHEET-v*-*.md"))
check("L-SHEET reads 'confirm the one final sheet' and names the newest version (v%d) A, B and SOURCE" % NEWV0, any(l.startswith("| L-SHEET (was Q10)") and "Confirm the one final owner sheet" in l and ("OWNER-SHEET-v%d-A.md" % NEWV0) in l and ("OWNER-SHEET-v%d-B.md" % NEWV0) in l and ("OWNER-SHEET-v%d-SOURCE.md" % NEWV0) in l for l in txt))
# section 9 duplicates
s9 = txt[[i for i, l in enumerate(txt) if l.startswith("## 9.")][0]:]
b9 = [l for l in s9 if l.startswith("- ")]
dup = [x[:60] for i, x in enumerate(b9) if any(x[:70] == y[:70] for y in b9[:i])]
check("section 9 has no duplicate bullet (%d bullets)" % len(b9), not dup, dup)
check("G12 named as open with the studio lead in section 9", any("G12" in l and "OPEN" in l for l in b9))
# box rules
terms = ["contact", "send", "same id", "n8n", "stand-in", "loopback re-smoke", "take", "rehearsal", "run sheet", "risks list", "rehearsal list", "studio lead", "owner", "lease", "alert", "gate", "re-pin", "public post", "ready", "wave 1", "table rule on the contact id", "k3b"]
low = box.lower()
wtt = low.index("what to type")
wyn = low.index("words you need (")
bad = []
for t in terms:
    first = re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(t), low)
    d = re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(t) + r"( and [a-z0-9 ]+?)? ?=", low)
    # c6s: a term is defined in the word list; its first use may come earlier ONLY in the WHAT TO TYPE block (which says the words are explained below) or with an inline gloss 'term =' or 'term ('
    early_ok = first and first.start() < wyn and wtt <= first.start() and "are explained in the lists below" in low[wtt:wyn]
    if not d or (first and first.start() < d.start() and t not in ("send", "take", "ready", "wave 1") and not early_ok and not low[first.end():first.end() + 3].startswith(" =")):
        bad.append((t, bool(d), box[first.start():first.start() + 30] if first else None))
check("every word the box defines is defined in the word list and first used before that only inside the WHAT TO TYPE block, which points to the lists (%d terms)" % len(terms), not bad, bad)
ix = intro.lower()
check("the box begins with the roles (2 lines) and the what-to-type block precedes the first word list", box.find("WHAT TO TYPE") > 0 and box.find("WHAT TO TYPE") < box.find("WORDS YOU NEED ("), "")
lq = box.find("| Label | Plain question")
fl = [m.group(0) for m in re.finditer(r"L-[A-Z]+", box)]
check("question labels are first used in the table of questions, except in the what-to-type block that names the two OWNER ONLY ones", lq >= 0 and bool(fl) and [m.start() for m in re.finditer(r"L-[A-Z]+", box) if m.start() < box.find("QUESTIONS (label") and not (box.find("WHAT TO TYPE") <= m.start() < box.find("WORDS YOU NEED ("))] == [], fl[:1])
bw = len(boxs.split())   # c6t: the short start box only (the detail is section 1c)
p = H + "/handover/core-hardening/c6-skip-audit/REPORT-c6p.md"
pw = None
if os.path.exists(p):
    pr = rd(p)
    pw = len(pr[pr.index("## Start here"):pr.index("## 0. Failures")].split())
check("c6t N5: the start box is under 2,500 words (c6s: 3,488; %d words now) and states its own real count" % bw, bw < 2500 and ("This box holds %d words" % bw) in boxs, bw)
sets = re.findall(r"saveDataSuccessExecution|saveManualExecutions|EXECUTIONS_DATA_SAVE", box)
check("box names no n8n setting", not sets, sets)
check("box has one answer line with seconds, three free names, the exception form and L-SHEET apart", "2026-11-16T18:00:00Z = 23:30:00 IST" in box and "builder: builder-A; reviewers: reviewer-B, reviewer-C" in box and "except L-KILL: b" in box and "Neither can be put on the line of step 2" in box and box.count("## ANSWER (studio lead,") == 1)
W1 = len(ready) + len(onlyq)
W1c = W1
check("box wave 1 count equals ready + defaults (%d)" % W1, ("%d wave 1 rows" % W1) in box, W1)
check("box says it edits the flow files and changes no running n8n; box says the lease sentence is not put in owner sheet or release note by the rows", "changes no running n8n" in box and "no row edits the owner sheet or the release note" in box)
check("box says steps 4 to 6 have no duration", "No file gives a duration for steps 4 to 6" in box)
check("L-SCENES question is gone", "| L-SCENES | studio lead" not in full and not any("L-SCENES" in r["st"] for r in rows))
check("rows 25, 37, 38 and 76 exist as rows", all(k in bylead for k in (25, 37, 38, 76)))
check("generator rule on rows 62 to 69 and row 92 edits the generator", all("GENERATOR RULE" in bylead[k]["why"] for k in range(62, 70)) and bylead[92]["f"].endswith("build_mainframe.py"))
check("section 8 has the coverage of the c6p, c6o and c6n reviews", "COVERAGE OF THE c6p REVIEWS" in full and "COVERAGE OF THE c6o REVIEWS" in full and "COVERAGE OF THE c6n REVIEWS" in full)
# files untouched
import hashlib
for nm in ("REPORT-c6o.md", "REPORT-c6p.md"):
    pass

# ---------------------------------------------------------------- c6r checks (the c6q reviews and the independent evidence of c6q)
import datetime as _dt
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MON = {"Nov": 11, "Dec": 12}
wbad = []
wn = 0
for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{1,2}) (Nov|Dec)\b(?: (\d{4}))?", raw):
    yr = int(m.group(4)) if m.group(4) else 2026
    wn += 1
    if WD[_dt.date(yr, MON[m.group(3)], int(m.group(2))).weekday()] != m.group(1):
        wbad.append(m.group(0))
check("every weekday written with a date is the true weekday (%d pairs; year 2026 unless written; no pair outside old-text quotes is skipped)" % wn, not wbad and wn >= 8, wbad[:4])
# the independent evidence named 'Tue 23 Nov' and 'Thu 18 Nov' as missed mutations: both are checked here as absent
check("no 'Tue 23 Nov' and no 'Thu 18 Nov' anywhere", "Tue 23 Nov" not in raw and "Thu 18 Nov" not in raw)
# caption row 21: no lease sentence by default
r21 = bylead[21]["new"]
check("row 21 (scene 3 caption) carries no lease sentence (no 'lease', no '45', no 'longer than', no 'claim')", not re.search(r"(?i)lease|\b45\b|longer than|we make this claim|for a longer gap", r21), r21[:140])
# counts: every statement of a count equals the computed value
cnt_bad = []
for m in re.finditer(r"(\d+) (?:rows )?(?:apply on the default|apply on the default of)", raw):
    if int(m.group(1)) != len(onlyq):
        cnt_bad.append(m.group(0))
for m in re.finditer(r"\b(\d+) (?:wave 1 rows|rows in all)", raw):
    if int(m.group(1)) != W1c:
        cnt_bad.append(m.group(0))
for m in re.finditer(r"wave 1 \((?:[^)]*?)\), (\d+) rows", raw):
    if int(m.group(1)) != W1c:
        cnt_bad.append(m.group(0))
check("every 'N apply on the default', 'N wave 1 rows' and 'N rows in all' equals the computed value (%d default-only, %d wave 1)" % (len(onlyq), W1c), not cnt_bad, cnt_bad[:5])
check("no stale count 91 or 42 stated as a wave 1 or default-only count", not re.search(r"\b91 (?:wave 1 )?rows\b|\b42 apply|\bthe 42 rows\b|\bon defaults only 42\b", raw), re.findall(r".{20}\b91 (?:wave 1 )?rows\b.{10}|.{20}\b42 apply.{10}", raw)[:3])
check("the box does not carry the old '58 s' card length", "58 s" not in box and "about 58" not in box)
check("row 14 (and the card rows 13, 14) carry no '(within 45 seconds)'", all("within 45" not in bylead[k]["new"] for k in (13, 14, 21)))
check("'one alert' is not stated as a fact about the take's flows in any new text (rows 13, 14, 74 and the box card text)", all(("sends one alert" not in bylead[k]["new"]) for k in bylead) and "it sends one alert" not in box, "")
# M-A: the approval gate and the mandatory repeat
i12 = bylead[8]["new"]
check("M-A: row 8 item 12 gates card line 1 and the caption on 'lease wording approved' with UTC and IST, and makes the repeat sent more than 45 seconds after the first mandatory", "lease wording approved" in i12 and "UTC and IST" in i12 and "more than 45 seconds after the first send" in i12 and "mandatory" in bylead[8]["why"], "")
check("M-A: the stop rules table has the lease wording approval entry", "| Lease wording approval (risks list item 12) |" in raw)
# M-C: Q27 reading is labelled the report's assumption; L-DEL does not say the open part is answered
check("M-C: Q27 reading labelled as the report's own assumption and OWNER-OPEN (ORD:232) in the box, row 8 and section 9", "MY ASSUMPTION" in box and "ORD:232" in box and "strictest reading" in bylead[8]["new"] and "OWNER-OPEN" in raw.split("## 9.")[1], "")
ldel = [l for l in txt if l.startswith("| L-DEL")]
check("M-C: L-DEL rows say 'ANSWERED' only for the part that is answered and say the delete-path criterion is open", all("Still open" in l or "open" in l for l in ldel) and any("ORD:232" in l for l in ldel), len(ldel))
# M-D: the real-key scan
i15 = bylead[6]["new"]
check("M-D: the key reaches the scan by a pattern file in memory or standard input from the key store; never a command line; never on disk; a hit means cancel or replace the key and treat the runs as compromised", all(x in i15 for x in ["pattern file that exists only in memory or through standard input", "never on a command line", "never saved to disk", "cancels or replaces that key at once", "compromised"]), "")
check("M-D: item 16 repeats the search for real key values", "This scan after the deletion also searches for the real key values" in i15, "")
# M-E: successful runs apply, failed runs wait, row 92 sets error none
check("M-E: rows 53, 55, 62, 64, 66, 68 wait for L-SAVEERR; row 92 keeps the failed-run setting none; row 44 says successful runs", all("waits for the answer of L-SAVEERR" in bylead[k]["st"] for k in (53, 55, 62, 64, 66, 68)) and '"saveDataErrorExecution": "none"' in bylead[92]["new"] and "successful run" in bylead[44]["new"], "")
check("M-E: L-SAVEERR is in the box and in section 3 with default No", any(l.startswith("| L-SAVEERR |") for l in box.split("\n")) and any(l.startswith("| L-SAVEERR | OWNER ONLY") and "| No |" in l for l in txt), "")
# C-4a on the default application: the failed-run setting stays none
d2 = {}
for r in rows:
    if "n8n-flows-real-v5/mf-" in r["f"] and r["f"].endswith(".json") and r["i"] not in waits:
        d2.setdefault(r["f"], rd(real(r["f"])))
        fl = d2[r["f"]].split("\n")
        k = r["old"].count("\n") + 1
        seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
        if seg.count(r["old"]) == 1:
            fl[r["ln"] - 1:r["ln"] - 1 + k] = [seg.replace(r["old"], r["new"], 1)]
            d2[r["f"]] = "\n".join(fl)
dd = [(os.path.basename(f), t.count('"saveDataSuccessExecution": "all"'), t.count('"saveDataErrorExecution": "all"'), t.count('"saveManualExecutions": false')) for f, t in d2.items()]
check("C-4a (defaults only): the four flow files then save successful runs (all) and not failed runs, manual false, once each", len(dd) == 4 and all(x[1:] == (1, 0, 1) for x in dd), dd)
# M-F: one construction
check("M-F: one construction (checked above); the box says so", "one construction" in box.lower(), "")
# naive M1/M5/M6
check("naive M1: 'take' is defined as the filmed run and 'the recovery flow claims the contact again' is used instead of 'takes over'", "TAKE = the one filmed run" in box and "claim the contact again" in box and "take over" not in raw.replace("does NOT take over; only the recovery flow does", ""), (box.count("claim the contact again"), raw.count("take over")))
check("naive M5: the claim table is named in the box and every code word of the box is explained or replaced (K3B, K3, C-3 to C-9, G12 are defined)", all(x in box for x in ["CLAIM TABLE", "G12 =", "K3B", "THE CHECKS", "CUT NUMBER"]), "")
check("naive M6: the box starts with a one-screen WHAT TO TYPE block before the first word list", box.find("WHAT TO TYPE") >= 0 and box.find("WHAT TO TYPE") < box.find("WORDS YOU NEED (") and box.find("WORDS YOU NEED (") - box.find("WHAT TO TYPE") < 2200, "")
# the box: UTC with IST on the example time (coordinator item 4); no time example without IST within 40 characters
ex = [m.start() for m in re.finditer(r"23:30", box)]
check("every '23:30' example time in the box has 'IST' within 40 characters (%d places)" % len(ex), ex and all("IST" in box[i:i + 40] for i in ex), len(ex))
# the owner-sheet facts: the real v29 files, their times and the check time
NEWV = max(vs)
sw = glob.glob(STEPS + "/OWNER-SHEET-v%d-*.md" % NEWV)
sw_names = sorted(os.path.basename(f) for f in sw)
check("the real v%d files on disk are %s and the report names every one of them" % (NEWV, sw_names), sw_names == ["OWNER-SHEET-v%d-%s.md" % (NEWV, x) for x in ("A", "B", "SOURCE")] and all(n in raw for n in sw_names), sw_names)
for f in sorted(sw):
    t_ = datetime.datetime.fromtimestamp(os.path.getmtime(f), datetime.timezone.utc)
    print("INFO %s last written %s UTC; check time of the report %s" % (os.path.basename(f), t_.strftime("%H:%M:%S"), ct))
check("source-copy statement: the report says the rows were checked against the scratchpad copy, that equality with the real files is unverified, and that 89 of the 94 rows cannot be read in the repository", "scratchpad/c6/tree/handover" in raw.split("## 1.")[0] and "UNVERIFIED" in raw.split("## 1.")[0] and "89 of the 94 rows" in raw.split("## 1.")[0], "")
nrepo = sum(1 for r in rows if os.path.exists(H + "/" + r["f"]))
check("89 rows of 94 name a file that is not in the repository (recounted: %d rows readable in the repo)" % nrepo, nrepo == 5 and N - nrepo == 89, nrepo)
# no pipe-in-cell: no row text holds a raw table border
check("no row old or new text holds a raw '|' (it would break its table cell)", all("|" not in r["rawold"] and "|" not in r["rawnew"] for r in rows), [r["i"] for r in rows if "|" in r["rawold"] or "|" in r["rawnew"]])
# untouched files
for nm in ("REPORT-c6q.md", "REPORT-c6p.md"):
    check("%s was not changed by this run (it is older than the build of REPORT-c6t.md and holds its own title line)" % nm, os.path.getmtime(H + "/handover/core-hardening/c6-skip-audit/" + nm) < os.path.getmtime(R) and rd(H + "/handover/core-hardening/c6-skip-audit/" + nm).startswith("# REPORT-" + nm[7:10]), "")
check("row 6 item 12 checks that the sheet's made-up domain and marker equal the ones of the risks list item 11 before any deletion instruction", "made-up e-mail domain and the name marker by which the sheet tells the owner to find leftover contacts must be exactly the ones" in bylead[6]["new"], "")
_bl = [l for l in box.split("\n") if l.startswith("| L-SHEET |")]
_wr = [(os.path.basename(f), datetime.datetime.fromtimestamp(os.path.getmtime(f), datetime.timezone.utc).strftime("%H:%M:%S")) for f in sorted(sw)]
_has = lambda txt_, n_, t_: len(re.findall(re.escape(n_) + r" \([^)]{0,40}?written " + re.escape(t_) + " UTC", txt_))
check("the box line of L-SHEET and the section 0 bullet each print every real v%d file with its real written time (UTC): %s" % (NEWV, _wr), len(_bl) == 1 and all(_has(_bl[0], n_, t_) == 1 and _has(raw.split("## 1.")[0], n_, t_) >= 1 for n_, t_ in _wr), _wr)
# ---------------------------------------------------------------- c6s checks (the c6r reviews)
sec0 = raw.split("## 1.")[0]
sec1b = raw[raw.index("## 1b."):raw.index("## 2. ")]
# F4: newest version rules (fail on a newer sheet, a higher version, a higher release note)
m_ = re.search(r"NEWEST OWNER SHEET VERSION NAMED IN THIS REPORT: v(\d+) \(at the check time (\d\d:\d\d:\d\d) UTC = (\d\d:\d\d:\d\d) IST\); NEWEST RELEASE NOTE NAMED: v(\d+)\.", raw)
rnv = sorted(int(re.search(r"v(\d+)", os.path.basename(f)).group(1)) for f in glob.glob(STEPS + "/LEAD-RELEASE-NOTE-v*.md") if "SOURCE" not in f)
check("F4 the report names the newest owner sheet version (v%d) and release note (v%d) on disk, and the check time" % (NEWV, rnv[-1]), bool(m_) and int(m_.group(1)) == NEWV and int(m_.group(4)) == rnv[-1] and m_.group(2) == ct[11:19], (m_.groups() if m_ else None, NEWV, rnv[-1]))
hi = [f for f in glob.glob(STEPS + "/*") if re.search(r"(OWNER-SHEET|LEAD-RELEASE-NOTE)-v(\d+)", f) and int(re.search(r"-v(\d+)", f).group(1)) > (NEWV if "OWNER-SHEET" in f else rnv[-1])]
check("F4 no owner sheet or release note has a version higher than the one named", not hi, hi)
check("F4 release note v14 is cited for G12 as still open (LRN14:33, LRN14:8) and the short name LRN14 is defined", "LRN14:33" in sec0 and "LRN14:8" in raw and "| LRN14 |" in raw and "LRN14:33" in box and "does not close it" in sec0, "")
check("F4 the wider reading of G12 ('processed once' beside a crash scene) is labelled the report's own assumption in the box, row 8 and section 9", "this report's own reading" in box and "this report's own reading" in bylead[8]["why"] and any("own assumption" in l and "G12" in l for l in b9), "")
check("F4 the owner-sheet check covers v19 and later (static-checks.sh globs v19 and v2x to v9x and lists a v31+ check)", "v[2-9]" in rd(os.path.dirname(os.path.abspath(__file__)) + "/static-checks.sh") and "modification time of every owner sheet file v28 and later" in cs, "")
# F1
c4a = [l for l in txt if l.startswith("| C-4a |")][0]
c11 = [l for l in txt if l.startswith("| C-11 |")][0]
c4l = [l for l in txt if l.startswith("| C-4 | Import check")][0]
check("F1 C-4a says failed-run saving is none on the defaults, all only after L-SAVEERR yes", "saveDataErrorExecution none" in c4a and "error-all 0" in c4a and "error-none 1" in c4a and "L-SAVEERR answered yes" in c4a, "")
check("F1 C-11 says PLAN:125 is overridden on failed runs and the lead sets ON_ERROR=none", "overridden" in c11 and "EXECUTIONS_DATA_SAVE_ON_ERROR=none" in c11 and "PLAN:125" in c11, "")
check("F1 C-4 row list is rows 63, 65, 67, 69 and 92 (not 62 to 68)", "rows 63, 65, 67, 69 and 92" in c4l and "63, 62" not in c4l, "")
lsv = [l for l in txt if l.startswith("| L-SAVE | studio lead")]
check("F1 L-SAVE (section 3), the box and section 9 say the plan is OVERRIDDEN on failed runs", len(lsv) == 1 and "OVERRIDDEN" in lsv[0] and "overridden" in box and any("PLAN:125" in l and "overrid" in l for l in b9), "")
check("F1 the glossary says the take uses all for successful and none for failed runs", "all for successful runs and none for failed runs" in raw, "")
# F2
check("F2 card line 2 gate in row 8 (item 12) and in the stop-rule table", "CARD LINE 2 GATE" in bylead[8]["new"] and any(l.startswith("| Card line 2, the alert sentence") for l in txt), "")
check("F2 the box and row 14 say card line 2 waits for an alert mail seen in the loopback re-smoke", "card line 2 stays blocked until the loopback re-smoke" in box and "gated" in bylead[14]["why"], "")
# F3
i15_ = bylead[6]["new"]
i16_ = i15_[i15_.index("16. AFTER THE TAKE"):]
check("F3 item 15 runs after EVERY rehearsal with real accounts", "After EVERY rehearsal with real accounts" in i15_, "")
check("F3 the scanner is read by a second person and tested with a fake key before it touches a real key", "is read by a second person (someone who did not write the scan) and tested with a fake key before it touches a real key" in i15_, "")
check("F3 counts only; no file holds the key or matched lines; not in the process list or shell history", "prints counts only: no file holds the key or any matched line" in i15_ and "not in the list of running programs and not in the shell history" in i15_, "")
check("F3 searches in place or on a dump that is deleted and counted to 0", "in place" in i15_ and "dump" in i15_ and "the count must be 0" in i15_, "")
check("F3 swap point named", "SWAP POINT" in i15_ and "standard input" in i15_ and "swap is off or encrypted" in i15_, "")
check("F3 item 16 scans BEFORE anything is deleted, writes counts, and scans once more after the deletion", i16_.index("BEFORE anything is deleted") < i16_.index("deletes every saved run") and "once more after the deletion" in i16_, "")
check("F3 the stop-rule row and check C-6 carry the same rules", any(l.startswith("| Real-key scan") and "after EVERY rehearsal" in l and "BEFORE anything is deleted" in l and "fake key" in l for l in txt) and "second person (someone who did not write the scan) who reads it and tests it with a fake key" in [l for l in txt if l.startswith("| C-6 |")][0], "")
check("F3 row 6 reason says items 11 to 16", "items 11 to 16" in bylead[6]["why"] and "items 11 to 14" not in bylead[6]["why"], "")
# m1..m4
check("m1 the approval of row 8 must cite the crash-then-repeat-during-recovery case with 1 row and 1 mail", "a crash is" not in "" and "while the recovery flow is still working on it" in bylead[8]["new"] and "1 row and 1 mail" in bylead[8]["new"], "")
check("m2 row 13 says 'expected to be true until C-9 part 2'", "expected to be true for a second send until C-9 part 2" in bylead[13]["why"] and "so the plain statement is true for a second send" not in bylead[13]["why"], "")
cut_ = re.findall(r"125 s", raw)
check("m3 the cut-case totals (125 s, 79 words, 31.6 s, 35 s, about 160 s) are given once, in the box CUT CASE; elsewhere only a pointer", raw.count("25 s + 40 s + 60 s = 125 s") == 1 and "25 s + 40 s + 60 s = 125 s" in box and "about 125 s of scenes" not in raw and "CUT CASE" in box and "Old cell text: 30 s EST" in box and "New cell text: 40 s EST" in box and "35 s EST" in box, len(cut_))
exs = re.findall(r"## ANSWER \([^)]*, (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) = ", box)
check("m4 every example answer time in the box is later than the check time %s (and has its IST)" % ct, bool(exs) and all(e > ct for e in exs) and "EXAMPLE" in box, exs)
# naive items
check("naive: the order of the reviewer names is explained", "ORDER of the two reviewer names matters" in box, "")
check("naive: the 'does not do' list comes before the answer line", box.index("does NOT do") < box.index("## ANSWER ("), "")
check("naive: ONE OWNER-ONLY rule: the section 3 rule line, the box and the L-SHEET and L-SAVEERR rows say only the owner answers", "never answers for him" in raw and all(any(l.startswith(k) and "OWNER ONLY" in l for l in txt) for k in ("| L-SAVEERR |", "| L-SHEET (was Q10)")) and "studio lead may answer for him" not in raw, "")
check("naive: the answer form puts L-SHEET and L-SAVEERR on separate OWNER lines", "L-SHEET v30A" in box and "L-SAVEERR yes" in box and "Neither can be put on the line of step 2" in box, "")
check("naive: Q27 (a), (b), (c) and G12 are explained in the box and the reader is addressed as 'you'", "Q27 (a), (b), (c) = your plan's three questions" in box and "G12 = YOUR gate" in box and "You are the STUDIO LEAD" in box, "")
steps = sec1c[sec1c.index("1c-F"):]
check("naive: numbered steps exist for rows 23, 58, 59, the G12 approval and the 45-second sentence (named who)", all(x in steps for x in ["applies row 23", "applies rows 58 and 59", "TASK (9) A QUESTION TO YOU", "TASK (10) approve the lease wording (G12)"]), "")
check("naive: the C-9 part 2 circle is explained", "THE CIRCLE IN C-9 PART 2" in box and "the approval rests on that look" in box, "")
check("naive: 'take' is not used for 'claim' and 'claim' is not used for a spoken statement of the video except in quotation", "may take it again" not in raw and not [l for l in txt if "reserved for the run that took it first" in l and "the plain sense of 'take'" not in l] and "THE TWO CLAIMS" not in raw and "unlimited claim" not in raw and "takes the 45-second limit out" not in raw, "")
check("naive: 'alert' is defined as a warning mail the system is built to send, not as a tested fact", "a warning mail the system is built to send" in box and "a warning mail the system is built to send" in raw.split("| alert |")[1][:300], "")
check("naive: stale names fixed (c6s supersedes c6r; L-SAVEERR in the glossary label row; 'items 11 to 16')", raw.startswith("# REPORT-c6t:") and "supersedes REPORT-c6s.md" in raw.split("\n")[0] and "L-SAVE, L-SAVEERR, L-PAGE" in raw, "")
check("naive: table 5a lists row 11 and says the 37 rows are a different group from the 36", any(l.startswith("| 11 | run sheet") for l in a5.split("\n")) and "37 rows of the run sheet" in a5 and "different group from the 36 rows" in a5, "")
check("naive: the section 0 history is moved after the how-to (section 1b exists after section 1 and before section 2)", raw.index("## 1b.") > raw.index("## 1. ") and raw.index("## 1b.") < raw.index("## 2. ") and "HISTORY, c6q" in sec1b and "HISTORY, c6q" not in sec0 and "HISTORY, c6r" in sec1b, "")
check("naive: EGM, KEY, FINAL, RUN, CHECK, ROW are defined in the box", all(x in box for x in ["EGM = ", "KEY = ", "FINAL = ", "RUN = ", "CHECK = ", "ROW = "]), "")
check("section 8 has the COVERAGE OF THE c6r REVIEWS block and c6s-CHANGES.md exists and maps every finding id", "COVERAGE OF THE c6r REVIEWS" in raw and os.path.exists(H + "/handover/core-hardening/c6-skip-audit/c6s-CHANGES.md") and all(x in rd(H + "/handover/core-hardening/c6-skip-audit/c6s-CHANGES.md") for x in ["F1", "F2", "F3", "F4", "m1", "m2", "m3", "m4", "M1", "M8"]), "")
check("section 9 holds the new open items (PLAN:125 conflict, leak scan program not written, card line 2 backed by stand-in tests only)", any("PLAN:125" in l and "overrides" in l for l in b9) and any("leak scan program" in l for l in b9) and any("Card line 2" in l and "stand-in" in l for l in b9), "")
check("section 9 old items are closed or rewritten, not left stale (3,490-word box, history order)", not any("3,490 words" in l and "[needs-lead]" in l for l in b9) and not any("Section 0 starts with history" in l and "[needs-lead]" in l for l in b9), "")
check("REPORT-c6r.md, REPORT-c6q.md and REPORT-c6p.md were not changed by this run", all(os.path.getmtime(H + "/handover/core-hardening/c6-skip-audit/" + n_) < os.path.getmtime(R) for n_ in ("REPORT-c6r.md", "REPORT-c6q.md", "REPORT-c6p.md")), "")
