# part 5 of verify-c6x.py (c6x): class 8 = the defects of the c6w reviews (review-c6w-design.md, review-c6w-naive.md, review-c6w-evidence.md).
# Every check here reads the START BOX ALONE (boxs = the text between '## Start here: what I need' and '## Start here, part 2') where the claim is about the box
# (design M2: the c6w checks read box + section 1c, so a claim 'in the box' could be true only of section 1c).
import filecmp, difflib
_b = boxs                      # the start box alone
_hdr = raw.split("\n", 4)      # the first lines of the report
# C8-1 (naive M1, design M2): the box says that no reviewer has read the report and that the reach of G12 is the report's own reading
check("C8-1 the start box alone says that no reviewer has read this report and that the reach of G12 is this report's own reading",
      "NO REVIEWER HAS READ THIS REPORT" in _b and "reach of G12" in _b and "own reading" in _b, "")
# C8-2 (design M1, naive M3): the four held items are all named in item 6 of the box, and the hand cut gives 76 words
_i6 = [l for l in _b.split("\n") if l.startswith("6. WHAT THE DEFAULTS LEAVE")]
check("C8-2 item 6 of the start box names all four held items (card line 1, 'other lease settings', the scene 3 caption, the label 'setting: lease 45 s') and the 76-word card",
      len(_i6) == 1 and all(x in _i6[0] for x in ("card line 1", "other lease settings", "scene 3 caption", "setting: lease 45 s", "76 words", "30.4 s")) and "cuts nothing by hand" not in raw, len(_i6))
# C8-3 (design M1): the 76 words are recomputed from the quoted card lines, and Table B has the case and row 96 names it
_wl = [len(q.split()) for q in Q]
_w76 = sum(_wl[1:]) - len("other lease settings".split())
_tb = [l for l in txt if l.startswith("| G12 open, every held item cut by hand")]
_tbc = [x.strip() for x in _tb[0].strip("|").split(" | ")] if _tb else []
check("C8-3 the 76-word case is recomputed from the four quoted lines (%d words without line 1 and without 'other lease settings'), %.1f s, budget %d s, and Table B and row 96 carry it" % (_w76, _w76 / 150 * 60, int(_w76 / 150 * 60 // 5 + 1) * 5),
      _w76 == 76 and len(_tbc) >= 7 and _tbc[2] == str(_w76) and _tbc[3] == "%.1f" % (_w76 / 150 * 60) and _tbc[4] == "35 s" and "76 words, 30.4 s" in bylead[96]["why"], _tbc[:5])
# C8-4 (naive M4): the refusal form and the 'closed' form are in the box
check("C8-4 the start box alone gives the three G12 forms (approved, not approved, closed: line 33 of release note v14 is my approval)",
      all(x in _b for x in ("): approved: ", "): not approved`", "): closed: line 33 of release note v14 is my approval`")), "")
# C8-5 (naive M5): the two owner-open items about the take script have a label, a question and an answer cell in the box
_qr = {}
for _l in _b.split("\n"):
    _m = re.match(r"^\| (L-Q27|L-DELCRIT|L-KEYLINE) \| ([^|]+) \| ([^|]+) \|$", _l)
    if _m:
        _qr[_m.group(1)] = (len(_m.group(2).split()), len(_m.group(3).split()))
check("C8-5 the start box has a row with label, question and answer for L-Q27, L-DELCRIT and L-KEYLINE (%s) and the OPEN ones say OWNER-OPEN" % _qr,
      set(_qr) == {"L-Q27", "L-DELCRIT", "L-KEYLINE"} and all(a >= 6 and b >= 3 for a, b in _qr.values()) and _b.count("OWNER-OPEN") >= 2, _qr)
# C8-6 (design M5): card line 3 holds no number of databases, and L-ONEDB says what it bars
_l3 = Q[2] if len(Q) >= 3 else ""
check("C8-6 card line 3 names one place ('n8n's own database') and no number of databases or stores; L-ONEDB says its scope and the open conflict",
      "own database" in _l3 and not re.search(r"\b(one|two|three|both|single|\d+)\b[^.]{0,20}\b(databases?|stores?)\b", _l3, re.I)
      and any("SCOPE OF THIS RULE" in l and "card line 3" in l.lower() for l in txt if l.startswith("| L-ONEDB (")), _l3[:80])
# C8-7 (naive M9): the typed line says that the three names are chosen by the studio lead
check("C8-7 the start box says that builder-A, reviewer-B and reviewer-C are names the studio lead chooses and that no program reads the line", "NAMES YOU CHOOSE" in _b and "No program reads this line" in _b, "")
# C8-8 (naive M8): the counts of the stop lists are recomputed: 7 stop steps, 11 gate rows of section 3e
_k3 = raw.index("3e. STOP RULES")
_gr = []
_st = False
for _l in raw[_k3:].split("\n"):
    if _l.startswith("| Check (where"):
        _st = True
        continue
    if _st:
        if _l.startswith("|---"):
            continue
        if _l.startswith("| "):
            _gr.append(_l)
        else:
            break
_stop7 = len(re.findall(r"rehearsal list items 11 to 15", sec1c)) >= 1 and "risks list items 11 and 12" in sec1c
_kk = [l for l in sec1c.split("\n") if l.startswith("- SEVEN STOP STEPS AND ELEVEN GATE ROWS")]
check("C8-8 section 3e has %d gate rows; section 1c-K says ELEVEN and SEVEN, and the section 9 reconciliation says eleven" % len(_gr),
      len(_gr) == 11 and len(_kk) == 1 and "ELEVEN gate rows" in _kk[0] and "SEVEN stop steps" in _kk[0] and _stop7 and "eleven gate rows in section 3e" in raw, len(_gr))
# C8-9 (the brief): the first lines say what failed, what is uncertain and what was not run
_fl = raw.split("\n")[2] if len(raw.split("\n")) > 2 else ""
check("C8-9 the first lines of the report say what failed, what is uncertain and what was not run, and that no reviewer has read it",
      _fl.startswith("WHAT FAILED, WHAT IS UNCERTAIN, WHAT I DID NOT RUN") and "FAILED:" in _fl and "UNCERTAIN:" in _fl and "NOT RUN:" in _fl and "NO REVIEWER HAS READ THIS REPORT" in _fl, _fl[:60])
# C8-10 (brief: readable in chunks): the two appendix files are the same text as the marker lines say, and each file is small enough to read
_here = os.path.dirname(os.path.abspath(R))
_ok10 = True
_det = []
if INCLUDED:
    _ok10 = sorted(INCLUDED) == ["REPORT-c6x-COVERAGE.md", "REPORT-c6x-TABLE.md"]
    for _f in INCLUDED:
        _sz = os.path.getsize(os.path.join(_here, _f))
        _det.append((_f, _sz))
        _ok10 = _ok10 and _sz < 200000
    _ok10 = _ok10 and os.path.getsize(R) < 200000 and len(rows) == 104 and "## 5. EDIT TABLE" in raw and "## 8. Coverage:" in raw
check("C8-10 the report is split into the main file and two appendix files, each under 200,000 bytes, the assembled text holds all 104 rows (%s)" % _det, _ok10 if INCLUDED else True, _det)
# C8-11 (design M4): the late files are compared by script; the report says what the script finds
_late = sorted(glob.glob(os.environ.get("C6V_STEPS_LIVE", "/nonexistent") + "/*.md"))
_cmp = []
for _f in _late:
    _n = os.path.basename(_f)
    _m = re.match(r"(OWNER-SHEET|LEAD-RELEASE-NOTE)-v(\d+)(.*)\.md$", _n)
    if not _m or "SOURCE" in _n:
        continue
    _pv = os.path.join(STEPS, "%s-v%d%s.md" % (_m.group(1), int(_m.group(2)) - 1, _m.group(3)))
    if os.path.exists(_pv):
        _a = rd(_pv).replace("v%d" % (int(_m.group(2)) - 1), "v%d" % int(_m.group(2)))
        _same = _a == rd(_f)
        _say_same = ("%s was written" % _n in raw) and re.search(re.escape(_n) + r" was written \d\d:\d\d:\d\d UTC = \d\d:\d\d:\d\d IST; equal to", raw) is not None
        _say_diff = re.search(re.escape(_n) + r" was written \d\d:\d\d:\d\d UTC = \d\d:\d\d:\d\d IST; DIFFERENT from", raw) is not None
        _cmp.append((_n, _same, _say_same, _say_diff))
check("C8-11 for every late file (%d compared) the report says 'equal to' only if the file is equal after the version number is changed, and 'DIFFERENT from' otherwise (recomputed now)" % len(_cmp),
      all((s and sa and not sd) or ((not s) and sd and not sa) for _n, s, sa, sd in _cmp), _cmp)
# C8-12 (naive M7): the statement of each run of run_all.sh is in section 9 and does not hide an unclean run
_rs = [l for l in raw.split("\n") if "STATEMENT OF EACH RUN" in l]
check("C8-12 section 9 holds one statement of each run of run_all.sh, names the build that wrote the report and says that the output files are written after the report",
      len(_rs) == 1 and "WHICH BUILD WROTE THIS REPORT: evidence-c6x/build_c6x.py" in _rs[0] and "written after REPORT-c6x.md" in _rs[0], len(_rs))
# C8-13 (naive minors): dates for 'tonight', no stale label
check("C8-13 the words 'tonight or tomorrow morning IST' stand only with their dates, and the report names no 'drift report for c6v' (stale label)",
      all("(that is Mon 16 Nov at night or Tue 17 Nov 2026 in the morning, IST)" in l for l in raw.split("\n") if "tonight or tomorrow morning IST" in l) and "drift report for c6v" not in raw, "")
# C8-14 (naive M2): the box and L-SHEET do not call a version 'newest at the check time'
check("C8-14 no text calls a version 'the newest at the check time' (the newest is named 'before the freeze')", "the newest at the check time" not in raw and "Newest at the check time" not in raw, "")
# C8-15 (coordinator, evidence runner): repeated numbers are compared in EVERY copy: the census holds the count of each card number and of the gate phrase
_cn = {p: raw.count(p) for p in ("90 words", "about 36 s", "budget 40 s", "87 words", "34.8 s", "79 words", "31.6 s", "76 words", "30.4 s", "74 words", "29.6 s", "lease wording approved")}
_cw = json.load(open(_E + "/census-c6x.json")) if os.path.exists(_E + "/census-c6x.json") else {}
check("C8-15 the census holds the count of every copy of each card number and of 'lease wording approved' (%s)" % _cn, all(_cw.get(p) == n and n >= 1 for p, n in _cn.items()) if _cw else False, {p: (_cw.get(p), n) for p, n in _cn.items() if _cw.get(p) != n})
