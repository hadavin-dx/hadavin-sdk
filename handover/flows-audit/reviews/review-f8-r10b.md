# F8 r10b diff review, round 2 (egm-codebase-details, agent a475d07; saved condensed; reviewer words unverified). Did not read check_flows.py; nothing ran.
Majors (no Blockers):
Q1 take-warns.pin:2 "reviewed by: flows-audit session ... lead to confirm" is accepted (take_check.sh:203-204 rejects only PLACEHOLDER); line 208 prints "KNOWN DEFECTS ... a person read and accepted" every run; pin hash covers only WARN lines so reviewer line editable undetected. Fix: print "reviewed by (as written in the pin): ..."; reject reviewer line containing "session" or "lead to confirm"; or state first exit 0 is not a person's review.
Q2 four-file sha256 computed (lines 74-80) after the checker ran (line 57); files re-read later; never compared. Fix: hash before and after, exit 4 if different, or run on a copy in TMP. sha256sum failure prints empty hash without MISSING; extra *.json not in sha.
Q3 run_all.sh line 230 prints exit status before line 235 may set RC=1 (printed 0, real 1).
Q4 tcfail (104-114) prints only "want exit 4, got N"; misleading "overwritten by another run" cause; inherits caller TAKE_CHECK_* env (use env -u); wanted-line match can pass for another reason.
Q5 checker exit >=4 (127, 137) returned as is; README:25 says --write-warn-pin ALWAYS exits 4 but it gives 2, 1, or checker code.
Held: exit 0 turned to 4 when PROBLEMS non-empty; real FAIL stays 1; pin writer refuses existing/symlink/in-use file; no fill_flows value printed.
