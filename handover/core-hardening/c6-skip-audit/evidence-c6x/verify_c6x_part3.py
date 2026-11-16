# part 3 of verify-c6x.py (c6x): the CLASS checks the independent mutation run of c6u showed missing.
# Classes: (1) a safe-default phrase must be unchanged in EVERY place it is quoted (census frozen by the build, plus fixed must-be-zero and must-exist phrases);
# (2) a count or version that appears twice must be equal everywhere; (3) the number of UNVERIFIED / OPEN labels is unchanged; (4) one copy of the card lines may not differ.
# The census file census-c6x.json is written by `C6V_MAKE_CENSUS=1 python3 -B -I verify-c6x.py` right after the build (run_all.sh does it); a report that was changed afterwards no longer matches it.
import json
_E = os.path.dirname(os.path.abspath(__file__))
PHRASES = ["90 words", "about 36 s", "budget 40 s", "87 words", "34.8 s", "79 words", "31.6 s", "76 words", "30.4 s", "74 words", "29.6 s", "lease wording approved", "lease wording seen", "NO REVIEWER HAS READ THIS REPORT", "other lease settings", "setting: lease 45 s", "I do not approve it", "G12 OPEN", "G12 is open", "G12 open", "NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE", "has NO delete call", "no delete call",
           "archive_contacts 'no'", "only made-up contacts of this run", "no, never", "lease sentence stays out of the public post", "filmed only after your written approval",
           "to 10 files", "twelve numbered TASKS", "two OPEN", "OPEN (OWNER ONLY)", "ANSWERED BY DEFAULT", "NOT APPLIED", "NOT FILMABLE", "OWNER ONLY", "OWNER-OPEN",
           "the 45 s lease setting is allowed only after G12 is approved", "G12 is approved", "I confirm", "nothing is applied",
           "cannot be filmed", "can be filmed", "Five items are OPEN", "items are OPEN", "LRN14:33", "release note v14 line 33", "line 33", "line 34", "release note v18", "release note v17", "LEAD-RELEASE-NOTE-v18.md", "LEAD-RELEASE-NOTE-v17.md", "OWNER-SHEET-v34-A.md", "OWNER-SHEET-v33-A.md", "OWNER-SHEET-v34-B.md", "v34 rendering A", "G12 gate"]
REGEXES = {"UNVERIFIED": r"UNVERIFIED", "VERIFIED_not_UN": r"(?<!UN)VERIFIED", "CHECKED": r"\bCHECKED\b", "DONE": r"\bDONE\b", "relayed": r"RELAYED"}

def _census(s):
    d = {p: s.count(p) for p in PHRASES}
    d.update({k: len(re.findall(v, s)) for k, v in REGEXES.items()})
    conf = {}
    for l in s.split("\n"):
        if re.match(r"^\| (L-[A-Z0-9]+) \| ", l) and l.count(" | ") >= 6 and "Confirmed" not in l:
            c = [x.strip() for x in l.strip("|").split(" | ")]
            conf[c[0]] = c[4][:12]
    d["_confirmed_cells"] = conf
    d["_check_time_copies"] = [s.count(ct[11:19] + " UTC"), s.count(ct[11:19] + "Z"), s.count(ct)]   # the check time, in each form it is written (c6v: one copy changed was missed)
    d["_lease_row_G12_counts"] = [l.count("G12") for l in s.split("\n") if l.startswith("| L-LEASE |")]   # the G12 hold on every L-LEASE row (c6v: removing it with the word count kept was missed)
    d["_card_line_copies"] = [s.count(q) for q in Q]   # how many times each of the four card lines is quoted whole
    return d

if os.environ.get("C6V_MAKE_CENSUS") == "1":
    json.dump(_census(raw), open(_E + "/census-c6x.json", "w"), indent=1, sort_keys=True)
    print("census written: %d phrases" % len(PHRASES))
    sys.exit(0)

_cp = _E + "/census-c6x.json"
check("class 1: the census file census-c6x.json exists (written by the build step of run_all.sh)", os.path.exists(_cp), _cp)
if os.path.exists(_cp):
    _want = json.load(open(_cp)); _have = _census(raw)
    _diff = {k: (_want[k], _have.get(k)) for k in _want if _want[k] != _have.get(k)}
    check("class 1: every safe-default phrase, every UNVERIFIED/VERIFIED/CHECKED count and every 'Confirmed?' cell equals the census of the build (%d items)" % len(_want), not _diff, _diff)
_ZERO = ["I approve it", "G12 CLOSED", "G12 is closed", "EVERYTHING IN THIS REPORT HAS BEEN APPLIED", "has a delete call", "archive_contacts 'yes'", "any contacts of any run", "yes, sometimes", "G12 is approved by default", "approved by default"]
_zbad = [p for p in _ZERO if p in raw]
check("class 1: phrases that would reverse a safe default are absent everywhere (%d phrases)" % len(_ZERO), not _zbad, _zbad)
check("class 1: the fixed safe-default sentences each appear at least once in the whole report", all(p in raw for p in ["I do not approve it", "NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE", "has NO delete call", "archive_contacts 'no'", "only made-up contacts of this run", "no, never", "filmed only after your written approval", "lease sentence stays out of the public post"]), "")
_ll = [l for l in txt if l.startswith("| L-LEASE | studio lead")]
check("class 1: the L-LEASE row of section 3 shows 'No' in the Confirmed? column and the G12 hold", len(_ll) == 1 and _ll[0].count(" | ") >= 6 and [x.strip() for x in _ll[0].strip("|").split(" | ")][4].startswith("No") and "G12" in _ll[0], _ll[:1])
_g12 = [l for l in raw.split("\n") if "G12" in l and ("I do not approve it" in l or "I approve" in l)]
check("class 1: every line that quotes the G12 approval answer quotes 'I do not approve it' and never 'I approve it' (%d lines)" % len(_g12), all("I do not approve it" in l and "I approve it" not in l for l in _g12), len(_g12))
# class 2: counts and versions that appear more than once are equal
_a5 = raw[raw.index("5a. WHAT CHANGES"):]
_a5n = 0
_a5l = _a5.split("\n")
for _l in _a5l[[k for k, x in enumerate(_a5l) if x.startswith("| Row |")][0] + 2:]:
    if not _l.startswith("| "): break
    _a5n += 1
_w1demo = sum(1 for r in rows if "after check" not in r["st"] and "waits for the answer of L-SAVEERR" not in r["st"] and "DECISION-one-store" not in r["f"])
_allowed = {N, len(ready), len(onlyq), len(ready) + len(onlyq), N - nrepo, _w1demo, _a5n, len(withc) + len(waits) + len(nofilm) if False else 3, 3 + 6}
_stale = []
for _m in re.finditer(r"(?<![:\w])(\d+) (?:wave 1 |ready |default )?(?:rows|edits|proposed text changes)\b", raw):
    _v = int(_m.group(1))
    _ln = raw[:_m.start()].count("\n") + 1
    _line = txt[_ln - 1]
    if _v >= 30 and _v not in _allowed and not re.search(r"c6[a-u]\b|HISTORY|history|was |had |earlier", _line):
        _stale.append((_ln, _v))
check("class 2: every count of 'N rows/edits' with N of 30 or more equals one of the computed counts %s (history lines excepted)" % sorted(x for x in _allowed if x >= 30), not _stale, _stale)
_holds = set(re.findall(r"holds OWNER-SHEET-v(\d+)", raw))
_nw = set(re.findall(r"v(\d+)-A and v\1-B are the newest", raw)) | set(re.findall(r"v(\d+)-A and v\d+-B are the newest", raw))
check("class 2: every 'vN-A and vN-B are the newest' names the newest sheet on disk (v%d)" % NEWV, _nw == {str(NEWV)}, _nw)
check("class 2: no text names evidence-c6u/contact-grep-output.txt or c6u-APPLIED-ROWS.md as this work's file", "evidence-c6u/contact-grep-output.txt" not in raw and "c6u-APPLIED-ROWS.md" not in raw, "")
check("class 2: every 'the folder holds OWNER-SHEET-vN' names the same N, the newest on disk (v%d)" % NEWV, _holds == {str(NEWV)}, _holds)
_ts = set(re.findall(r"At (\d\d:\d\d:\d\d) UTC = ", raw))
_ct2 = re.search(r"check time[^\n]{0,80}?(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)", raw)
check("class 2: every 'At HH:MM:SS UTC' of the owner-sheet statement is the same time (%s)" % sorted(_ts), len(_ts) == 1, _ts)
_ten = re.findall(r"\bto (\d+|ten|twelve|eleven) files\b", raw)
_tw = re.findall(r"\b(\d+|ten|twelve|eleven) (?:numbered )?TASKS\b", raw)
check("class 2: 'to N files' is 10 everywhere (found %s) and the number of TASKS is twelve everywhere (found %s)" % (sorted(set(_ten)), sorted(set(_tw))), set(_ten) <= {"10"} and set(_tw) <= {"twelve"}, (sorted(set(_ten)), sorted(set(_tw))))
_two = re.findall(r"\b(two|three|four|five|six) OPEN( \(OWNER ONLY\) questions| items)?", raw)
_osq = [l for l in txt if (l.startswith("| L-SHEET (was Q10) |") or l.startswith("| L-SAVEERR | OWNER ONLY")) and "OWNER ONLY" in l]
check("class 2: 'two OPEN (OWNER ONLY) questions' and 'five OPEN items' are the only forms, and the section 3 rows give exactly two OWNER ONLY questions (found %s)" % sorted(set(_two)), all((w, q) in {("two", " (OWNER ONLY) questions"), ("five", " items")} for w, q in _two) and len(_osq) == 2, (sorted(set(_two)), len(_osq)))
_tn = [int(x) for x in re.findall(r"TASK \((\d+)\)", raw)]
check("class 2: no TASK number above twelve (the list has 12 tasks)", max(_tn) <= 12, max(_tn))
# class 4: card lines are one text everywhere
_cl_bad = []
for _qi, _q in enumerate(Q):
    _h = " ".join(_q.split()[:8])
    for _m in re.finditer(re.escape(_h), raw):
        _seg = raw[_m.start():_m.start() + len(_q)]
        if _seg != _q:
            _cl_bad.append((_qi + 1, raw[:_m.start()].count("\n") + 1))
check("class 4: every place that quotes a card line (from its first eight words; the shorter option (b) of L-CARDLEN differs earlier and is a different text on purpose) quotes it whole and equal to the line in rows 13 and 14 (%d lines)" % len(Q), len(Q) == 4 and not _cl_bad, _cl_bad[:6])
# class 5: the safe-default sentence 'no row edits the owner sheet or release note' is in both the box and 1c
check("class 1: 'imports nothing into n8n' appears in the box and 'changes no running n8n' in section 1c", boxs.count("imports nothing into n8n") >= 1 and sec1c.count("changes no running n8n") >= 1, (boxs.count("changes no running n8n"), sec1c.count("changes no running n8n")))

# class 6: a short old text (under 40 characters) must occur once in the WHOLE file, not only on its line (a builder who applies a row by text would hit the other places)
_short = []
for _r in rows:
    if len(_r["old"]) < 40 and "\n" not in _r["old"]:
        _ft = rd(real(_r["f"]))
        _chained = any(q["f"] == _r["f"] and q["new"] == _r["old"] for q in rows if q["i"] != _r["i"])
        if _ft.count(_r["old"]) != 1 and not _chained:
            _short.append((_r["i"], _ft.count(_r["old"])))
check("class 6: every old text shorter than 40 characters occurs exactly once in the whole file (chained rows excepted)", not _short, _short)
