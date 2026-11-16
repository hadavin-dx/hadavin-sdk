# c6r global text patches. exec()d by build_c6r.py after the box is inserted, before the file is written.
def gsub(old, new, c=1):
    n = sum(l.count(old) for l in L)
    assert n == c, "gsub expected %d, found %d: %r" % (c, n, old[:80])
    for i, l in enumerate(L):
        if old in l:
            L[i] = l.replace(old, new)


# ---- plain words: "take over" is not used; the recovery flow claims the contact again
gsub("the recovery flow may take over a contact that is not finished:", "the recovery flow may claim a contact that is not finished again:")
gsub("a second send does not take over; c6q WITHDRAWS that guess:", "a second send does not claim the contact again; c6q withdrew that guess, and c6r keeps it withdrawn (a second send is not the recovery flow; the recovery flow does claim again):")
gsub("the time after which the recovery flow may take over a contact that is not finished.", "the time after which the recovery flow may claim a contact that is not finished again.")
gsub("which the recovery flow may take over (JR:26)", "which the recovery flow may claim again (JR:26)")
gsub("given that the recovery flow may take over a crashed contact?", "given that the recovery flow may claim a crashed contact again?")
# ---- the checker name
gsub("verify-c6q", "verify-c6r", c=sum(l.count("verify-c6q") for l in L))
gsub("the 72 edits can be applied", "the 94 edits can be applied")
# ---- M-B: "one alert" only for the stand-in tests
gsub("it sends one alert, a warning mail that asks a person to look.", "it sends an alert, a warning mail that asks a person to look.")
gsub("so it sends one alert and a person decides", "so in our stand-in tests it sent one alert and a person decides", c=sum(l.count("so it sends one alert and a person decides") for l in L))
# ---- counts (the 42 rows that wait only for a question; the 36 now; the 6 rows that wait for L-SAVEERR)
for i, l in enumerate(L):
    l2 = re.sub(r"and the 42 rows that wait only for a question \([^)]*\), 91 rows in all", "and the %d rows that wait only for a question (%s), %d rows in all" % (len(onlyq), lst(onlyq), W1), l)
    l2 = l2.replace("the take saves every run (flow-file rows, the generator, saving notes)", "the take saves every successful run (flow-file rows, the generator, saving notes; saving of failed runs waits for L-SAVEERR)")
    l2 = l2.replace("and 42 apply on the default of a question you have not answered (section 3);", "and 36 apply on the default of a question you have not answered (section 3);")
    L[i] = l2
patch("| TOTAL |", "ready 49, on defaults only 42, with a check 3, NOT FILMABLE until an answer 0", "ready %d, on defaults only %d, with a check %d, waiting for the answer of L-SAVEERR %d (default no), NOT FILMABLE until an answer 0" % (len(ready), len(onlyq), len(withc), len(waits)))
i = find("0. Failures") if False else find("- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED.")
L[i] = sub(L[i], "42 apply on the default of a question you have not answered (section 3); 3 wait for a check that needs n8n (rows 23, 58, 59);",
           "%d apply on the default of a question you have not answered (section 3); 3 wait for a check that needs n8n (rows 23, 58, 59); %d wait for the answer of L-SAVEERR, whose default is no, so 'apply all defaults' does not apply them (rows %s);" % (len(onlyq), len(waits), lst(waits)))
patch("3c. 'APPLY ALL DEFAULTS'", "and the 3 rows", "and the 3 rows", 0) if False else None
# 3c: add the rows that wait
i3 = find("3c. 'APPLY ALL DEFAULTS'")
L[i3] = L[i3].replace("Rows it does not apply: 23, 58, 59 (wait for a check).", "Rows it does not apply: 23, 58, 59 (wait for a check) and %s (wait for the answer of L-SAVEERR, default no)." % lst(waits), 1)
assert "wait for the answer of L-SAVEERR, default no" in L[i3], "3c rows that wait"

# ---- section 0: the c6q reviews and the independent evidence, the source copy, the labels
ip = find("- THE LAST REPORT (REPORT-c6p.md) FAILED INDEPENDENT REVIEW:")
rest = L[ip].split("The main faults of c6p that c6q corrects:", 1)[1]
L[ip] = "- HISTORY, c6p (REPORT-c6p.md FAILED INDEPENDENT REVIEW): review-c6p-design.md (1 blocker, 7 majors, minors), review-c6p-naive.md (0 blockers, 6 majors, 10 minors) and evidence-c6p-independent/00-SUMMARY.md. c6q fixed these; the main faults of c6p were:" + rest
inew = ip
NEWQ = ("- THE LAST REPORT (REPORT-c6q.md) FAILED INDEPENDENT REVIEW: review-c6q-design.md (0 blockers, 6 majors M-A to M-F, minors), review-c6q-naive.md (0 blockers, 6 majors M1 to M6, minors) and evidence-c6q-independent/00-SUMMARY.md (its checks passed and listed 8 changes they did not catch and the stale owner-sheet line). THIS REPORT (c6r) HAS NOT BEEN REVIEWED YET by independent reviewers; I did not run the EGM steps (the studio lead runs them), and evidence-c6r/verify-c6r.py is mine: it proves the new text matches what I wrote and that listed slips are gone, not that a statement is true. The main faults of c6q that c6r corrects (the map from every finding to its fix is c6r-CHANGES.md): "
        "(1) the plain statement 'a second send is processed once' could go on the card and the caption before the studio lead approved the lease wording; now a gate (rehearsal and risks list, row 8 item 12) keeps card line 1 and the caption off the video until he writes 'lease wording approved' with UTC and IST, and a repeat sent more than 45 seconds after the first send is then mandatory; "
        "(2) card line 2 said 'it sends one alert' as a fact about the take's flows; it now says 'it sends an alert' and 'one alert' appears only for stand-in tests; "
        "(3) the meaning of Q27 (a), (b), (c) was written as the studio's rule; it is labelled as this report's assumption (the strictest reading), OWNER-OPEN as ORD:232 keeps it, and L-DEL no longer says 'ANSWERED' for the part that is open; "
        "(4) the scan for real key values said nothing about how the key reaches the search; it now says: from the key store, through a pattern file kept in memory or through standard input, never on a command line, never saved to disk, and a hit means cancel or replace the key and treat the runs as compromised; the scan is repeated after deletion (item 16); "
        "(5) saving of failed runs was bundled with saving of successful runs; the owner's words cover only successful runs, so failed runs are a new question L-SAVEERR (default no) and the six rows that set it wait; "
        "(6) the length table used two ways to build option (b); it now uses one; "
        "(7) the box used words before explaining them (take, recovery, claim table, check names, internal codes); it now opens with a one-screen 'what to type' block and explains each; 'take' means the filmed run of the whole video, and the recovery flow 'claims the contact again' instead of 'takes over'; "
        "(8) the owner-sheet line was stale: the check is rerun at the time stated below and the verifier fails if any v29 file changed after it; "
        "(9) the old words 'reading 1' and 'reading 2' are answer 1 and answer 2 of L-LEASE (they remain only in the history lines).")
L.insert(inew, NEWQ)
inr = find("- NOT DONE, NOT VERIFIED IN c6q (first):")
L[inr] = ("- NOT DONE, NOT VERIFIED IN c6r (first): nothing is applied; no n8n, flow, harness or stopwatch run exists; the seconds of the card are estimates from word counts; the facts of lease answer 2 are NOT TO BE SPOKEN AS FACT before C-9 part 2; the approval of the lease wording (gate G12, LRN:33; LREP:80) is OPEN with the studio lead; the meaning of Q27 (a), (b), (c) and the check of the delete path are OWNER-OPEN (ORD:232), and this report applies the strictest reading as its own assumption; the flows' behaviour was read from files and not run; the take script is not in the audited files; which owner sheet is final is not known. "
          "WHAT THE ROWS WERE CHECKED AGAINST: every old text was checked against a copy of the files in the build session's scratchpad folder (scratchpad/c6/tree/handover), not against the repository. Whether that copy equals the real files is UNVERIFIED. In the repository on branch cloud/core-hardening only inputs/DECISION-one-store.md can be read; the files of 89 of the 94 rows (the run sheet, the page statements, the start notes, mf.py, the four flow files, build_mainframe.py) cannot, so the builder must first confirm that each old text still occurs once in the real file.")
patch("- WHAT IS ABSENT FROM THE CHECKED FILES:", "Every path in this report is a path inside the repository.", "Every path in this report is the path the file has on that branch; the copy and the real files are not proven equal (see the entry before the first NOT RUN line).")

# ---- section 1: short name for the generator
ij = find("| JS | handover/demo/n8n-flows-real-v5/mf-sub-crm-mail.json")
L.insert(ij + 1, "| BMF | handover/demo/n8n-mainframe/build_mainframe.py | the program that writes the four real-v5 flow files (rows 62 to 69 and 92); its saving settings are the dictionary ST |")
patch("- READY =", "- READY =", "- READY =", 1) if False else None

# ---- section 3e: the stop rules of the new items
ie = find("| Execution list before scene 1 and scene 2 (row 23, check C-5)")
L[ie + 1:ie + 1] = [
    "| Real-key scan (rehearsal list items 15 and 16) | no real key value is found in any store, with the key read from the key store, through a pattern file in memory or standard input, never on a command line, never saved to disk; scans before the take, after the take and after deletion | studio lead | the owner, if a key was found | No: a hit means the key is cancelled or replaced with its provider, the runs made with it count as compromised, and the take does not start until a new key and a clean scan are written |",
    "| Lease wording approval (risks list item 12) | the studio lead has written 'lease wording approved' with the date and time in UTC and IST, and the repeat sent more than 45 seconds after the first send is written with its reply showing the repeat flag true | studio lead | the owner, if the card or caption must change | No: card line 1 and the scene 3 caption are not filmed without it |",
    "| Made-up domain and marker (rehearsal list item 12) | the made-up e-mail domain and the name marker on the owner sheet equal the ones in item 11 of the risks list | studio lead | the owner | No: no deletion instruction goes to the owner until they match |",
]
