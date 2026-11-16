P("## 6. The contact gate in detail (does the take delete or archive contacts? every cite below was opened)")
P("Words: ARCHIVE = HubSpot moves the contact to its recycle bin (it can be restored). PERMANENT DELETE = the contact is erased. TAKE SCRIPT = scripts/run_real_check_n8n.py, the program the video uses (on a local take branch that is never pushed; not in the checked files). OLD DESK TEST PROGRAM = scripts/run_real_check.py, an older program that is NOT the take. PROBE SCRIPT = scripts/hubspot_probe.py (a test of the HubSpot key). The studio lead's decision 2 (%s) says the take never deletes contacts; leftover made-up contacts are listed and the owner deletes them by hand in HubSpot after the take." % quote("DEC", "2. TAKE IDENTITY")[0])
P("")
P("WHAT IS ANSWERED (your answers in ORDERS.md): Q19 item 1 (%s): the take script has NO delete call and uses a read-only HubSpot identity with archive_contacts 'no' and lists leftovers; the 'archive in a finally' step that was read belongs to the OLD DESK TEST PROGRAM. Q23 (%s): decision 2 stays, the take never deletes; the independent review of 11:00 UTC (16:30 IST) found no delete or archive path in the take script; line 1051 of the plan is stale text; do not widen the HubSpot key. Q20 item 3: the scope of the HubSpot key is held by the owner and unknown to the studio; the studio lead asks the owner once at take prep. Q27 (%s): UNVERIFIED; the studio lead reads the take script at the final version and answers (a), (b) or (c) with line numbers at the re-pin." % (quote("ORD", "1. The take program")[0], quote("ORD", "Q23:")[0], quote("ORD", "Q27:")[0]))
P("")
P("WHAT IS STALE OR UNVERIFIED (the files still say it; no row may repeat it as program behaviour):")
P("")
P("| What the file says | Cite (opened) | Text at the cite | Status |")
P("|---|---|---|---|")
for lab, k, a, st in [
    ("Old help text: an option that archives the contacts the run made", "EQ4", "--cleanup", "Belongs to the old desk test program or is stale: not the take (Q19 item 1)"),
    ("Plan 4: up to 3 contacts archived at the end", "P4", "up to 3 HubSpot contacts archived at the end", "STALE notice (Q23); must not be shown to the owner; row %d item 11 says so" % n("rs59")),
    ("Plan 4: archives also when the take ends in an error; leftovers listed", "P4", "1. the script archives this take's contacts", "STALE (Q23, Q19 item 1)"),
    ("The probe script docstring and code (audit note)", "CA", "scripts/hubspot_probe.py:4-5", "The probe script is not the take; UNVERIFIED which key it uses"),
    ("The probe tries a permanent delete first, then an archive (audit note)", "CB", "hubspot_probe.py:271-287", "The probe script is not the take; script not in the tree"),
    ("Whether an archived contact keeps its e-mail address reserved", "SH", "ASSUMED to keep its email reserved", "ASSUMPTION, never checked"),
    ("Owner sheet v25 A: a notice line saying contacts will be deleted or archived is a difference; stop", "OS25", "Compare every number and name in the notice", "Consistent with Q23"),
    ("Owner sheet v25 A: the owner deletes made-up contacts by hand", "OS25", "You delete only made-up contacts of this run", "Consistent with decision 2"),
]:
    c, t = quote(k, a)
    P("| %s | %s | %s | %s |" % (lab, c, t, st))
P("")
P("Checked by reading the four real-v5 flow files (command and output: evidence-c6m/contact-grep-output.txt, copied from the c6k run): no DELETE call and no archive call (0 hits). The only places that touch contacts are the take script and the other scripts, and those files are not in the checked files.")
P("")
P("THE GATE (row %d, item 11 of the rehearsal list on the run sheet): before the take the studio lead reads the take script at the final version, runs two searches (one for the word archive, one for the word delete; I give two commands because the table cell must not hold a pipe character), writes the output on the run sheet, and writes a four-line record (version id; search output; 'matches the decision' or 'stop: tell the owner'; no notice that promises delete or archive is shown). Until then the take is blocked. The owner sheet may say that the owner deletes leftovers by hand; it must NOT say that the HubSpot key is read-only or create-and-change-only unless the owner confirmed it (Q20 item 3). The closing check is C-10 (section 7); it no longer requires the decisions file to have 0 hits, because decision 2 itself says never deletes." % n("rs59"))
P("")
