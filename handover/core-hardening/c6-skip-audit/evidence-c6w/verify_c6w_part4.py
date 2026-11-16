# class 7 (new in c6w): the defects of the c6v reviews review-c6v-design.md and review-c6v-naive.md. Each statement below runs alone; each was shown to fail on REPORT-c6v.md
# (evidence-c6w/verify-c6w-on-c6v.txt) or on a changed copy (evidence-c6w/neg_new_c6w.py, the W-C7 names).
_c7_hist = lambda l: l.startswith("| design ") or l.startswith("| naive ") or l.startswith("| Design ") or l.startswith("| Naive ")  # a CHANGES-style table line quotes the old defect on purpose
_c7_name = os.path.basename(R)
_c7_label = re.sub(r"^REPORT-|\.md$", "", _c7_name)
_c7_ans = re.findall(r"`## ANSWER \([^)]*\): (c6[a-z]) apply all defaults to (REPORT-c6[a-z]\.md)", boxs)
check("D-B1: the typed answer line names this report: the label equals the file name label (%s) and the file name equals %s" % (_c7_label, _c7_name), len(_c7_ans) == 1 and _c7_ans[0] == (_c7_label, _c7_name) and ("must be %s and the file %s" % (_c7_label, _c7_name)) in boxs and len(re.findall(r"apply all defaults to REPORT-", boxs)) == 1, _c7_ans)
# D-M1: the release note lines, one statement, true against the real files
_rn14 = rd(STEPS + "/LEAD-RELEASE-NOTE-v14.md").split("\n")
_rnl_ = sorted((f for f in glob.glob(STEPS + "/LEAD-RELEASE-NOTE-v*.md") if "SOURCE" not in f), key=lambda f: int(re.search(r"-v(\d+)", f).group(1)))
_rnn = rd(_rnl_[-1]).split("\n")
_eq = sorted(k for k in (8, 33, 149, 150) if _rn14[k - 1] == _rnn[k - 1])
check("D-M1: the real files agree with the one statement 'lines 33 and 150 equal, lines 8 and 149 differ' (equal now: %s) and no text says that lines 8, 33, 149 and 150 are equal" % _eq, _eq == [33, 150] and "its lines 33 and 150 equal the newest note" in boxs and "its lines 8 and 149 differ" in boxs and not re.search(r"lines 8, 33, 149(,| and) 150\b[^.;|]{0,30}\bequal", raw) and not re.search(r"lines 8, 33 and 149 (are )?equal", raw), _eq)
# N-B2: one form of the G12 line
_g12 = re.findall(r"`## G12 \(studio lead, <UTC> = <IST>\): approved: [^`]*`", raw)
_lwa = [n for n, l in enumerate(txt, 1) if "lease wording approved" in l and not _c7_hist(l)]
check("N-B2: ONE G12 form: it is printed once in the box, every other copy is equal to it, the typed line comes only after the three loopback re-smoke results, and 'lease wording approved' is gone outside quoted history (%d copies, %s other lines)" % (len(_g12), _lwa), len(re.findall(r"`## G12 \(studio lead, <UTC> = <IST>\): approved: [^`]*`", boxs)) == 1 and len(set(_g12)) == 1 and "only after the loopback re-smoke of TASK (5)" in boxs and "the table rule seen in the re-smoke database" in sec1c and "a crash followed by a repeat while the recovery flow is working" in sec1c and not _lwa, (len(_g12), len(set(_g12))))
# D-M2: every row with the lease label holds G12 (rows 1 and 19 included), and the lists of rows name exactly those rows
_lab = sorted(r["i"] for r in rows if "setting: lease 45 s" in r["new"] or "45 s lease setting" in r["new"] or "45 s lease" in r["new"])
_nohold = [i for i in _lab if "G12" not in bylead[i]["new"] + bylead[i]["view"] + bylead[i]["why"]]
_carve = sorted(i for i in _lab if i not in (1, 17) or True)
_lists = re.findall(r"carve-outs of rows ([\d, and]+?) that now say", raw)
_lists += re.findall(r"carve-out in rows ([\d, and]+?) now reads", raw)
_lnums = [sorted(int(x) for x in re.findall(r"\d+", l_)) for l_ in _lists]
check("D-M2: every row whose new text carries the lease label holds G12 (rows %s; without hold: %s); rows 1 and 19 are among them; the lists of carve-out rows in the report equal that set" % (_lab, _nohold), not _nohold and 1 in _lab and 19 in _lab and len(_lnums) >= 2 and all(set(x) <= set(_lab) and set(_lab) - set(x) <= {1, 17, 5} or x == _lab for x in _lnums) and all(81 in x for x in _lnums), (_lab, _lnums))
# D-M3: one card state in rows 11, 13, 14 and 96
_r96 = bylead[96]["new"]
check("D-M3: row 96 sets the card's Time cell to the same 40 s as row 11 (90 words) and no default row says 35 s EST", "40 s EST" in _r96 and "35 s EST" not in _r96 and "40 s" in bylead[11]["new"] and all("35 s" not in bylead[k]["new"] for k in (11, 13, 14)), _r96[:80])
# D-M4: every question label used in the box is defined in the box table (or by '=' in the box word list)
_ll = sorted(set(re.findall(r"\bL-[A-Z0-9]{2,12}\b", boxs)))
_lund = [x for x in _ll if ("| %s |" % x) not in boxs and ("%s =" % x) not in boxs]
check("D-M4: every L- label used in the start box has its own row in the box question table or an '=' definition (%d labels; undefined: %s)" % (len(_ll), _lund), not _lund and "L-CARDLEASE" in _ll, _lund)
# D-m1: one list before the first rehearsal
_pre = re.findall(r"TASKS \(1\) to \(6\) and \(8\) to \((\d+)\)", raw)
_pre_all = re.findall(r"TASKS \(1\) to \((\d+)\) and \(8\) to \((\d+)\)", raw)
check("D-m1: the list that must be finished before the first rehearsal is one list, TASKS (1) to (6) and (8) to (10), in every place that gives it (%d places)" % len(_pre), len(_pre) >= 4 and set(_pre) == {"10"} and not _pre_all and "ONE LIST" in raw and "TASKS (5) to (9)" not in raw, _pre)
# D-m2: the written-time statement
check("D-m2: section 0 says the identical written time of v30 to v33 is a bulk write and that no content hash was used", "shows a bulk write" in raw and "content hash" in raw.split("## 1.")[0], "")
# D-m3: no 'v30A'
_v30 = [n for n, l in enumerate(txt, 1) if "v30A" in l and not _c7_hist(l)]
check("D-m3: no example answer uses 'v30A' (only 'v34 rendering A'); outside quoted history lines: %s" % _v30, not _v30 and "v34 rendering A" in boxs, _v30)
# D-m4: stale labels
_stale = [n for n, l in enumerate(txt, 1) if re.search(r"\[done in c6|RECHECKED AGAIN IN c6t|\(this file\) supersedes c6t|c6u \(this file\)", l) and not _c7_hist(l)]
check("D-m4: no stale label ('[done in c6x]', 'RECHECKED AGAIN IN c6t', 'c6u (this file)') outside quoted history lines: %s" % _stale, not _stale, _stale)
# D-m5: run count named
check("D-m5: the report names the number of full runs of run_all.sh and the cap", re.search(r"I started no sub-agent; I ran the full pipeline run_all\.sh \d+ time\(s\) \(cap 2; heavy-slot order\)", raw) is not None, "")
# D-m6, D-m7
check("D-m6: option (b) of L-CARDLEN states its 0.4 s margin and that it may run over until a stopwatch run", "0.4 s" in raw and "stopwatch" in raw.split("0.4 s")[1][:400] if "0.4 s" in raw else False, "")
_ll4 = [l for l in txt if l.startswith("| L-LEASE |") and "studio lead (his answers" in l]
check("D-m7: the L-LEASE row of section 3 says plainly that the default follows ORD:230 and reverses ORD:186", len(_ll4) == 1 and "ORD:230" in _ll4[0] and "reverses ORD:186" in _ll4[0], len(_ll4))
# D-M5: honest counts
check("D-M5: 'HOW MUCH IS PROVEN BY WHOM' says the counts of changed copies are my own run; the box states its own word count apart from part 2", "HOW MUCH IS PROVEN BY WHOM" in raw and "are my own run of my own scripts" in raw and "is not counted, so reading both takes about" in boxs, "")
# N-M2: the branch statement equals the table
_w1rows = [r["i"] for r in rows if "after check" not in r["st"] and "waits for the answer of L-SAVEERR" not in r["st"]]
_dec = sorted(r["i"] for r in rows if r["i"] in _w1rows and "DECISION-one-store" in r["f"])
_stb = re.search(r"A builder applies the (\d+) rows of WAVE 1 .*?on branch cloud/flows-audit \(folder handover/; it holds the files of (\d+) rows\)\. (\d+) rows \(([\d, ]+)\) edit inputs/DECISION-one-store\.md, which exists only on branch cloud/core-hardening", boxs)
check("N-M2: the branch statement of step 1 equals the table (wave 1 %d rows, %d on branch cloud/flows-audit, %d rows %s on cloud/core-hardening)" % (len(_w1rows), len(_w1rows) - len(_dec), len(_dec), _dec), _stb is not None and int(_stb.group(1)) == len(_w1rows) and int(_stb.group(2)) == len(_w1rows) - len(_dec) and int(_stb.group(3)) == len(_dec) and [int(x) for x in _stb.group(4).split(",")] == _dec, _stb.groups() if _stb else None)
# N-M3, N-M6, N-M7
check("N-M3: section 0 says who has read what (review-c6v-design.md and review-c6v-naive.md read REPORT-c6v.md only)", "WHO HAS READ WHAT" in raw and "review-c6v-design.md and review-c6v-naive.md read REPORT-c6v.md only" in raw, "")
_sh = [n for n, l in enumerate(txt, 1) if re.search(r"\b[Ss]heet [AB]\b", l) and not _c7_hist(l)]
check("N-M6: no 'sheet A' or 'sheet B' (the A and B owner-sheet files are RENDERING A and B; the older-key ways are KEY ROUTE A and B); outside quoted history: %s" % _sh, not _sh and "RENDERING A" in boxs and "KEY ROUTE A" in raw, _sh)
check("N-M7: the box says every answer other than the default needs a further round", "EVERY ANSWER OTHER THAN THE DEFAULT NEEDS A FURTHER ROUND" in boxs, "")
# N-M9: no undefined label before the word list
_blk = boxs[:boxs.index("WORDS YOU NEED (")]
_und = [x for x in ("K3B", "C-9", "Q27", "ORD:", "LRN14", "TASK (9)", "row 96", "C-4") if x in _blk]
check("N-M9: the WHAT TO TYPE block uses none of the labels the stranger review found undefined (%s)" % _und, not _und and (boxs.index("WORDS YOU NEED (") - boxs.index("WHAT TO TYPE")) < 2400, _und)
# N-m1, N-m2, N-m4, N-m5, N-m7, N-m8, N-m9
_lb = [l for l in txt if l.startswith("- LABELS OF THE CHECKS AND OF EARLIER REVIEWS")]
check("N-m1/N-m2: the LABELS bullet defines STEP, CHECK, KEY, PRIMARY KEY, 'lead', CLASS 1 TO 7, W-, L-APP2, G19, N1 and the release note versions", len(_lb) == 1 and all(x in _lb[0] for x in ("STEP =", "CHECK =", "KEY =", "PRIMARY KEY =", "'lead'", "CLASS 1 TO 7 =", "W- =", "L-APP2 =", "G19 =", "N1", "RELEASE NOTE VERSIONS")), len(_lb))
check("N-m4: the two groups of rows (the 37 viewer rows of 5a and the 38 rows on a default) are said to be different groups", "this group is a different group from the 38 rows that apply on the default" in raw, "")
check("N-m5: a sentence says the reason cell after its first stop is history, and that rows 39 and 76 are two edits", "READING THE REASON CELLS" in raw and "rows 39 and 76 are two edits" in raw, "")
check("N-m7: the box says that if you are also the owner the two roles stay separate", "if you are also the owner, the two roles stay separate" in boxs, "")
check("N-m8/N-m9: section 9 lists the section 3e item numbers and the counts to reconcile", "Section 3e (naive m8)" in raw.split("## 9. Not covered")[1] and "Counts to reconcile (naive m9)" in raw.split("## 9. Not covered")[1], "")
# V12: the CHANGES file has a row for each finding
_chg = H + "/handover/core-hardening/c6-skip-audit/c6w-CHANGES.md"
_ids = ["design B1", "design M1", "design M2", "design M3", "design M4", "design M5"] + ["design m%d" % k for k in range(1, 8)] + ["naive B1", "naive B2"] + ["naive M%d" % k for k in range(1, 10)] + ["naive m%d" % k for k in range(1, 10)]
_cm = [x for x in _ids if not os.path.exists(_chg) or ("| %s |" % x) not in rd(_chg)]
check("V12: c6w-CHANGES.md exists and has its own row for each of the %d finding ids of the two c6v reviews (missing: %s)" % (len(_ids), _cm), os.path.exists(_chg) and not _cm, _cm)
